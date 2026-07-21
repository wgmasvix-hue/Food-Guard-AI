"""Compliance score calculation used by the dashboard.

The score blends four signals into a single 0-100 percentage:
  - GMP checklist pass rate (last 30 days)
  - Temperature logs within limits (last 30 days)
  - Corrective actions closed on time vs overdue
  - Audit findings resolved vs open

Each signal defaults to 100 when there is no data, so a brand-new company
starts at 100 rather than being penalized for having nothing recorded yet.
"""
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.audit import AuditFinding
from app.models.corrective_action import CorrectiveAction
from app.models.enums import CAStatus
from app.models.gmp import Checklist, ChecklistStatus
from app.models.temperature import TemperatureLog, TemperatureUnit


def _safe_ratio(numerator: int, denominator: int) -> float:
    return 100.0 if denominator == 0 else round(100.0 * numerator / denominator, 1)


def calculate_compliance_score(db: Session, company_id: str) -> float:
    since = datetime.now(timezone.utc) - timedelta(days=30)

    checklist_total = db.scalar(
        select(func.count(Checklist.id)).where(
            Checklist.company_id == company_id,
            Checklist.status == ChecklistStatus.COMPLETED,
            Checklist.completed_at >= since,
        )
    ) or 0
    checklist_passed = db.scalar(
        select(func.count(Checklist.id)).where(
            Checklist.company_id == company_id,
            Checklist.status == ChecklistStatus.COMPLETED,
            Checklist.completed_at >= since,
            Checklist.score >= 80,
        )
    ) or 0
    gmp_score = _safe_ratio(checklist_passed, checklist_total)

    temp_total = db.scalar(
        select(func.count(TemperatureLog.id))
        .join(TemperatureUnit, TemperatureLog.unit_id == TemperatureUnit.id)
        .where(TemperatureUnit.company_id == company_id, TemperatureLog.recorded_at >= since)
    ) or 0
    temp_within = db.scalar(
        select(func.count(TemperatureLog.id))
        .join(TemperatureUnit, TemperatureLog.unit_id == TemperatureUnit.id)
        .where(
            TemperatureUnit.company_id == company_id,
            TemperatureLog.recorded_at >= since,
            TemperatureLog.within_limits.is_(True),
        )
    ) or 0
    temp_score = _safe_ratio(temp_within, temp_total)

    ca_total = db.scalar(
        select(func.count(CorrectiveAction.id)).where(CorrectiveAction.company_id == company_id)
    ) or 0
    ca_overdue = db.scalar(
        select(func.count(CorrectiveAction.id)).where(
            CorrectiveAction.company_id == company_id,
            CorrectiveAction.status.in_([CAStatus.OPEN, CAStatus.IN_PROGRESS, CAStatus.OVERDUE]),
        )
    ) or 0
    ca_score = _safe_ratio(ca_total - ca_overdue, ca_total)

    finding_total = db.scalar(
        select(func.count(AuditFinding.id)).join(
            AuditFinding.audit
        ).where(AuditFinding.audit.has(company_id=company_id))
    ) or 0
    finding_open = db.scalar(
        select(func.count(AuditFinding.id))
        .join(AuditFinding.audit)
        .where(AuditFinding.audit.has(company_id=company_id), AuditFinding.status == "open")
    ) or 0
    audit_score = _safe_ratio(finding_total - finding_open, finding_total)

    weighted = (gmp_score * 0.3) + (temp_score * 0.3) + (ca_score * 0.25) + (audit_score * 0.15)
    return round(weighted, 1)
