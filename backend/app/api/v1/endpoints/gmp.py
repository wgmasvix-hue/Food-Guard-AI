from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_active_user, get_db
from app.core.rbac import require_min_role
from app.models.corrective_action import CorrectiveAction
from app.models.enums import CAStatus, ChecklistStatus, UserRole
from app.models.gmp import Checklist, ChecklistItem, ChecklistTemplate, ChecklistTemplateItem
from app.models.user import User
from app.schemas.gmp import (
    ChecklistRead,
    ChecklistStart,
    ChecklistSubmit,
    ChecklistTemplateCreate,
    ChecklistTemplateRead,
)

router = APIRouter()


# --- Templates ---

@router.get("/templates", response_model=list[ChecklistTemplateRead])
def list_templates(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return (
        db.query(ChecklistTemplate)
        .filter(
            ChecklistTemplate.is_active.is_(True),
            (ChecklistTemplate.company_id == current_user.company_id) | (ChecklistTemplate.company_id.is_(None)),
        )
        .order_by(ChecklistTemplate.category)
        .all()
    )


@router.post("/templates", response_model=ChecklistTemplateRead, status_code=status.HTTP_201_CREATED)
def create_template(
    payload: ChecklistTemplateCreate,
    current_user: User = Depends(require_min_role(UserRole.QA_MANAGER)),
    db: Session = Depends(get_db),
):
    items_data = payload.model_dump()["items"]
    template = ChecklistTemplate(company_id=current_user.company_id, **payload.model_dump(exclude={"items"}))
    template.items = [ChecklistTemplateItem(**item) for item in items_data]
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


# --- Checklists (inspections) ---

@router.get("/checklists", response_model=list[ChecklistRead])
def list_checklists(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return (
        db.query(Checklist)
        .filter(Checklist.company_id == current_user.company_id)
        .order_by(Checklist.created_at.desc())
        .limit(200)
        .all()
    )


@router.post("/checklists", response_model=ChecklistRead, status_code=status.HTTP_201_CREATED)
def start_checklist(
    payload: ChecklistStart,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    template = db.get(ChecklistTemplate, payload.template_id)
    if not template or (template.company_id and template.company_id != current_user.company_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

    checklist = Checklist(
        template_id=template.id,
        company_id=current_user.company_id,
        facility_id=payload.facility_id,
        inspector_id=current_user.id,
        status=ChecklistStatus.IN_PROGRESS,
        started_at=datetime.now(timezone.utc),
    )
    checklist.items = [
        ChecklistItem(
            template_item_id=item.id,
            question=item.question,
            is_critical=item.is_critical,
        )
        for item in template.items
    ]
    db.add(checklist)
    db.commit()
    db.refresh(checklist)
    return checklist


@router.get("/checklists/{checklist_id}", response_model=ChecklistRead)
def get_checklist(checklist_id: str, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    checklist = db.get(Checklist, checklist_id)
    if not checklist or checklist.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Checklist not found")
    return checklist


@router.post("/checklists/{checklist_id}/submit", response_model=ChecklistRead)
def submit_checklist(
    checklist_id: str,
    payload: ChecklistSubmit,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    checklist = db.get(Checklist, checklist_id)
    if not checklist or checklist.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Checklist not found")

    items_by_id = {item.id: item for item in checklist.items}
    failed_critical = []
    for submitted in payload.items:
        item = items_by_id.get(submitted.id)
        if not item:
            continue
        item.result = submitted.result
        item.comment = submitted.comment
        item.photo_path = submitted.photo_path
        if submitted.result == "fail" and item.is_critical:
            failed_critical.append(item)

    scored_items = [i for i in checklist.items if i.result in ("pass", "fail")]
    checklist.score = (
        round(100 * sum(1 for i in scored_items if i.result == "pass") / len(scored_items), 1)
        if scored_items else None
    )
    checklist.notes = payload.notes
    checklist.status = ChecklistStatus.FAILED if failed_critical else ChecklistStatus.COMPLETED
    checklist.completed_at = datetime.now(timezone.utc)

    for item in failed_critical:
        ca = CorrectiveAction(
            company_id=current_user.company_id,
            facility_id=checklist.facility_id,
            raised_by_id=current_user.id,
            title=f"GMP failure: {item.question[:80]}",
            issue_description=item.comment or f"Critical checklist item failed: {item.question}",
            source="gmp",
            source_reference_id=checklist.id,
            evidence_photo_path=item.photo_path,
            status=CAStatus.OPEN,
        )
        db.add(ca)
        db.flush()
        item.corrective_action_id = ca.id

    db.commit()
    db.refresh(checklist)
    return checklist
