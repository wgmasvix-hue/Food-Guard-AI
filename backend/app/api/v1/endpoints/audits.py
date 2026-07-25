from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_active_user, get_db
from app.core.rbac import require_min_role
from app.models.audit import Audit, AuditFinding
from app.models.audit_template import AuditAIAnalysis, AuditChecklistItem, AuditTemplate, AuditTemplateItem
from app.models.corrective_action import CorrectiveAction
from app.models.enums import AuditStatus, CAStatus, SignatureMeaning, UserRole
from app.models.user import User
from app.schemas.audit import (
    AuditAIAnalysisRead,
    AuditChecklistItemSubmit,
    AuditCreate,
    AuditFindingCreate,
    AuditFindingRead,
    AuditRead,
    AuditTemplateCreate,
    AuditTemplateRead,
    AuditUpdate,
)
from app.schemas.signature import SignatureCreate
from app.services.ai import get_ai_provider
from app.services.ai.audit_analysis import build_audit_analysis_prompt, parse_audit_analysis
from app.services.ai.prompts import AUDIT_ANALYSIS_SYSTEM_PROMPT
from app.services.signing import sign

router = APIRouter()


def _get_or_404(db: Session, audit_id: str, company_id: str) -> Audit:
    audit = db.get(Audit, audit_id)
    if not audit or audit.company_id != company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit not found")
    return audit


# --- Audit Templates ---

@router.get("/templates", response_model=list[AuditTemplateRead])
def list_audit_templates(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return (
        db.query(AuditTemplate)
        .filter(
            AuditTemplate.is_active.is_(True),
            (AuditTemplate.company_id == current_user.company_id) | (AuditTemplate.company_id.is_(None)),
        )
        .order_by(AuditTemplate.name)
        .all()
    )


@router.post("/templates", response_model=AuditTemplateRead, status_code=status.HTTP_201_CREATED)
def create_audit_template(
    payload: AuditTemplateCreate,
    current_user: User = Depends(require_min_role(UserRole.QA_MANAGER)),
    db: Session = Depends(get_db),
):
    items_data = payload.model_dump()["items"]
    template = AuditTemplate(company_id=current_user.company_id, **payload.model_dump(exclude={"items"}))
    template.items = [AuditTemplateItem(**item) for item in items_data]
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


# --- Audits ---

@router.get("", response_model=list[AuditRead])
def list_audits(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return (
        db.query(Audit)
        .filter(Audit.company_id == current_user.company_id)
        .order_by(Audit.scheduled_date.desc())
        .all()
    )


@router.post("", response_model=AuditRead, status_code=status.HTTP_201_CREATED)
def create_audit(
    payload: AuditCreate,
    current_user: User = Depends(require_min_role(UserRole.QA_MANAGER)),
    db: Session = Depends(get_db),
):
    audit = Audit(company_id=current_user.company_id, **payload.model_dump())
    db.add(audit)
    db.flush()

    if audit.template_id:
        template = db.get(AuditTemplate, audit.template_id)
        if not template or (template.company_id and template.company_id != current_user.company_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit template not found")
        audit.checklist_items = [
            AuditChecklistItem(
                template_item_id=item.id, clause=item.clause, question=item.question, is_critical=item.is_critical
            )
            for item in template.items
        ]

    db.commit()
    db.refresh(audit)
    return audit


@router.get("/{audit_id}", response_model=AuditRead)
def get_audit(audit_id: str, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return _get_or_404(db, audit_id, current_user.company_id)


@router.patch("/{audit_id}", response_model=AuditRead)
def update_audit(
    audit_id: str,
    payload: AuditUpdate,
    current_user: User = Depends(require_min_role(UserRole.AUDITOR)),
    db: Session = Depends(get_db),
):
    audit = _get_or_404(db, audit_id, current_user.company_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(audit, field, value)
    db.commit()
    db.refresh(audit)
    return audit


@router.post("/{audit_id}/findings", response_model=AuditFindingRead, status_code=status.HTTP_201_CREATED)
def add_finding(
    audit_id: str,
    payload: AuditFindingCreate,
    current_user: User = Depends(require_min_role(UserRole.AUDITOR)),
    db: Session = Depends(get_db),
):
    _get_or_404(db, audit_id, current_user.company_id)
    finding = AuditFinding(audit_id=audit_id, **payload.model_dump())
    db.add(finding)
    db.commit()
    db.refresh(finding)
    return finding


# --- Audit Checklist ---

@router.post("/{audit_id}/checklist/submit", response_model=AuditRead)
def submit_audit_checklist(
    audit_id: str,
    items: list[AuditChecklistItemSubmit],
    current_user: User = Depends(require_min_role(UserRole.AUDITOR)),
    db: Session = Depends(get_db),
):
    audit = _get_or_404(db, audit_id, current_user.company_id)
    items_by_id = {i.id: i for i in audit.checklist_items}

    for submitted in items:
        item = items_by_id.get(submitted.id)
        if not item:
            continue
        item.result = submitted.result
        item.comment = submitted.comment
        if submitted.result == "fail" and item.is_critical and not item.corrective_action_id:
            ca = CorrectiveAction(
                company_id=current_user.company_id,
                facility_id=audit.facility_id,
                raised_by_id=current_user.id,
                title=f"Audit failure: {item.question[:80]}",
                issue_description=item.comment or f"Critical audit checklist item failed: {item.question}",
                source="audit",
                source_reference_id=audit.id,
                status=CAStatus.OPEN,
            )
            db.add(ca)
            db.flush()
            item.corrective_action_id = ca.id

    scored = [i for i in audit.checklist_items if i.result in ("pass", "fail")]
    if scored:
        audit.score = round(100 * sum(1 for i in scored if i.result == "pass") / len(scored), 1)

    db.commit()
    db.refresh(audit)
    return audit


# --- Signed completion ---

@router.post("/{audit_id}/complete", response_model=AuditRead)
def complete_audit(
    audit_id: str,
    payload: SignatureCreate,
    request: Request,
    current_user: User = Depends(require_min_role(UserRole.AUDITOR)),
    db: Session = Depends(get_db),
):
    audit = _get_or_404(db, audit_id, current_user.company_id)
    if payload.meaning != SignatureMeaning.AUDIT_COMPLETION:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Wrong signature meaning for this action")

    content = f"audit:{audit.id}:score={audit.score}:findings={len(audit.findings)}:completed_by={current_user.id}"
    sign(
        db, request=request, current_user=current_user, payload=payload,
        entity_type="audit", entity_id=audit.id, content_to_hash=content,
    )

    audit.status = AuditStatus.COMPLETED
    audit.completed_date = date.today()
    db.commit()
    db.refresh(audit)
    return audit


# --- AI Analysis ---

@router.post("/{audit_id}/ai-analysis", response_model=AuditAIAnalysisRead)
async def generate_audit_analysis(
    audit_id: str,
    current_user: User = Depends(require_min_role(UserRole.AUDITOR)),
    db: Session = Depends(get_db),
):
    audit = _get_or_404(db, audit_id, current_user.company_id)

    provider = get_ai_provider()
    user_prompt = build_audit_analysis_prompt(audit)
    try:
        raw = await provider.complete(AUDIT_ANALYSIS_SYSTEM_PROMPT, user_prompt)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    parsed = parse_audit_analysis(raw)
    analysis = AuditAIAnalysis(
        audit_id=audit.id,
        generated_by_id=current_user.id,
        generated_at=datetime.now(timezone.utc),
        **parsed,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis


@router.get("/{audit_id}/ai-analysis", response_model=AuditAIAnalysisRead | None)
def get_latest_audit_analysis(
    audit_id: str, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    audit = _get_or_404(db, audit_id, current_user.company_id)
    return audit.ai_analyses[0] if audit.ai_analyses else None
