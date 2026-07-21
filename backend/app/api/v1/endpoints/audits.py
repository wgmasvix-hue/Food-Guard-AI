from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_active_user, get_db
from app.core.rbac import require_min_role
from app.models.audit import Audit, AuditFinding
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.audit import AuditCreate, AuditFindingCreate, AuditFindingRead, AuditRead, AuditUpdate

router = APIRouter()


def _get_or_404(db: Session, audit_id: str, company_id: str) -> Audit:
    audit = db.get(Audit, audit_id)
    if not audit or audit.company_id != company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit not found")
    return audit


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
