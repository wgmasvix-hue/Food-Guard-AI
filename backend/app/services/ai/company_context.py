"""Grounds AI chat answers in the asking user's real company data.

Small local models (the primary target here is self-hosted Ollama) have
unreliable native tool-calling, so rather than exposing function-calling
tools to the model, this module inspects the user's message for domain
keywords and pre-fetches the relevant slice of data as plain text,
injected into the prompt as context. If nothing matches, a compact
cross-module snapshot is used instead so the assistant always has
*something* concrete to ground an answer in.

Every query here is scoped to `company_id` — never cross-tenant. This is
the same multi-tenancy boundary every other endpoint in the app enforces.
"""
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.audit import Audit
from app.models.corrective_action import CorrectiveAction
from app.models.enums import CAStatus
from app.models.gmp import Checklist
from app.models.haccp import HaccpPlan
from app.models.temperature import TemperatureLog, TemperatureUnit
from app.services.search import search_documents

MAX_ROWS = 8
RECENT_DAYS = 7


def _open_corrective_actions(db: Session, company_id: str) -> str:
    rows = (
        db.query(CorrectiveAction)
        .filter(CorrectiveAction.company_id == company_id, CorrectiveAction.status != CAStatus.CLOSED)
        .order_by(CorrectiveAction.created_at.desc())
        .limit(MAX_ROWS)
        .all()
    )
    if not rows:
        return "Open corrective actions: none."
    lines = [
        f"- [{r.status}] {r.title} (source: {r.source or 'n/a'}, deadline: {r.deadline or 'not set'})" for r in rows
    ]
    return f"Open corrective actions ({len(rows)} shown, most recent first):\n" + "\n".join(lines)


def _recent_temperature_excursions(db: Session, company_id: str) -> str:
    since = datetime.now(timezone.utc) - timedelta(days=RECENT_DAYS)
    rows = (
        db.query(TemperatureLog)
        .join(TemperatureUnit, TemperatureLog.unit_id == TemperatureUnit.id)
        .filter(
            TemperatureUnit.company_id == company_id,
            TemperatureLog.within_limits.is_(False),
            TemperatureLog.recorded_at >= since,
        )
        .order_by(TemperatureLog.recorded_at.desc())
        .limit(MAX_ROWS)
        .all()
    )
    if not rows:
        return f"Temperature excursions (last {RECENT_DAYS} days): none."
    lines = [
        f"- {r.unit.name}: {r.temperature}°C at {r.recorded_at:%Y-%m-%d %H:%M} "
        f"(limits {r.unit.min_temp}-{r.unit.max_temp}°C)"
        for r in rows
    ]
    return f"Temperature excursions in the last {RECENT_DAYS} days:\n" + "\n".join(lines)


def _haccp_summary(db: Session, company_id: str) -> str:
    plans = db.query(HaccpPlan).filter(HaccpPlan.company_id == company_id).limit(MAX_ROWS).all()
    if not plans:
        return "HACCP plans: none on file."
    lines = [
        f"- {p.name} (status: {p.status}, {len(p.ccps)} CCPs, next review: {p.next_review_date or 'not set'})"
        for p in plans
    ]
    return f"HACCP plans ({len(plans)} shown):\n" + "\n".join(lines)


def _gmp_summary(db: Session, company_id: str) -> str:
    since = datetime.now(timezone.utc) - timedelta(days=14)
    rows = (
        db.query(Checklist)
        .filter(Checklist.company_id == company_id, Checklist.completed_at >= since)
        .order_by(Checklist.completed_at.desc())
        .limit(MAX_ROWS)
        .all()
    )
    if not rows:
        return "GMP inspections (last 14 days): none completed."
    lines = [
        f"- {r.template.name if r.template else 'Inspection'}: "
        f"score {r.score if r.score is not None else 'n/a'}% on {r.completed_at:%Y-%m-%d}"
        for r in rows
    ]
    return "Recent GMP inspections:\n" + "\n".join(lines)


def _audit_summary(db: Session, company_id: str) -> str:
    rows = db.query(Audit).filter(Audit.company_id == company_id).order_by(Audit.created_at.desc()).limit(MAX_ROWS).all()
    if not rows:
        return "Audits: none on file."
    lines = [
        f"- {r.title} ({r.audit_type}, {r.status}), score: {r.score if r.score is not None else 'n/a'}" for r in rows
    ]
    return f"Audits ({len(rows)} shown, most recent first):\n" + "\n".join(lines)


def _document_search_results(db: Session, company_id: str, message: str) -> str | None:
    """The actual retrieval step of retrieval-augmented generation: search
    the company's own documents (SOPs, policies, HACCP plans, etc.) for
    whatever the user just asked, so the model can cite real excerpts
    instead of guessing at content it's never seen."""
    results = search_documents(db, company_id, message, limit=3)
    if not results:
        return None
    lines = [f'- "{r.title}" ({r.category}): {r.snippet}' for r in results]
    return "Relevant excerpts from your documents:\n" + "\n".join(lines)


# Keyword -> section-builder routing. A message can match more than one.
_ROUTES: list[tuple[tuple[str, ...], callable]] = [
    (("temperature", "temp ", "cold room", "freezer", "fridge", "chiller"), _recent_temperature_excursions),
    (("haccp", "ccp", "critical control", "hazard"), _haccp_summary),
    (("gmp", "inspection", "checklist", "hygiene"), _gmp_summary),
    (("audit",), _audit_summary),
    (("corrective", "capa", "non-conformance", "nonconformance"), _open_corrective_actions),
]


def build_company_context(db: Session, company_id: str | None, message: str) -> str:
    """Return plain-text context relevant to `message`, or "" if there's
    no company to scope to (e.g. a Super Admin account)."""
    if not company_id:
        return ""

    lower = message.lower()
    sections = [fn(db, company_id) for keywords, fn in _ROUTES if any(k in lower for k in keywords)]

    if not sections:
        # No keyword matched — give a compact cross-module snapshot so the
        # assistant still has real data to ground a general question in.
        sections = [
            _open_corrective_actions(db, company_id),
            _recent_temperature_excursions(db, company_id),
            _audit_summary(db, company_id),
        ]

    doc_section = _document_search_results(db, company_id, message)
    if doc_section:
        sections.append(doc_section)

    return "\n\n".join(sections)
