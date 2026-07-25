from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_active_user, get_db
from app.models.corrective_action import CorrectiveAction
from app.models.enums import CAStatus, SignatureMeaning, UserRole
from app.models.user import User
from app.schemas.corrective_action import (
    CorrectiveActionCreate,
    CorrectiveActionRead,
    CorrectiveActionUpdate,
    CorrectiveActionVerify,
)
from app.schemas.signature import SignatureCreate
from app.services.signing import sign

router = APIRouter()


def _get_or_404(db: Session, ca_id: str, company_id: str) -> CorrectiveAction:
    ca = db.get(CorrectiveAction, ca_id)
    if not ca or ca.company_id != company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Corrective action not found")
    return ca


@router.get("", response_model=list[CorrectiveActionRead])
def list_corrective_actions(
    status_filter: str | None = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    query = db.query(CorrectiveAction).filter(CorrectiveAction.company_id == current_user.company_id)
    if status_filter:
        query = query.filter(CorrectiveAction.status == status_filter)
    return query.order_by(CorrectiveAction.created_at.desc()).all()


@router.post("", response_model=CorrectiveActionRead, status_code=status.HTTP_201_CREATED)
def create_corrective_action(
    payload: CorrectiveActionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    ca = CorrectiveAction(company_id=current_user.company_id, raised_by_id=current_user.id, **payload.model_dump())
    db.add(ca)
    db.commit()
    db.refresh(ca)
    return ca


@router.get("/{ca_id}", response_model=CorrectiveActionRead)
def get_corrective_action(ca_id: str, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return _get_or_404(db, ca_id, current_user.company_id)


@router.patch("/{ca_id}", response_model=CorrectiveActionRead)
def update_corrective_action(
    ca_id: str,
    payload: CorrectiveActionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    ca = _get_or_404(db, ca_id, current_user.company_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(ca, field, value)
    db.commit()
    db.refresh(ca)
    return ca


@router.post("/{ca_id}/verify", response_model=CorrectiveActionRead)
def verify_corrective_action(
    ca_id: str,
    payload: CorrectiveActionVerify,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if current_user.role not in (UserRole.QA_MANAGER, UserRole.FOOD_SAFETY_OFFICER, UserRole.COMPANY_ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only QA/Food Safety roles can verify")
    ca = _get_or_404(db, ca_id, current_user.company_id)

    content = f"corrective_action:{ca.id}:verified_by={current_user.id}"
    sign(
        db, request=request, current_user=current_user,
        payload=SignatureCreate(
            entity_type="corrective_action", entity_id=ca.id,
            meaning=SignatureMeaning.CORRECTIVE_ACTION_VERIFICATION, typed_name=payload.typed_name,
        ),
        entity_type="corrective_action", entity_id=ca.id, content_to_hash=content,
    )

    now = datetime.now(timezone.utc)
    ca.verification_notes = payload.verification_notes
    ca.verified_by_id = current_user.id
    ca.verified_at = now
    ca.closed_at = now
    ca.status = CAStatus.CLOSED
    db.commit()
    db.refresh(ca)
    return ca
