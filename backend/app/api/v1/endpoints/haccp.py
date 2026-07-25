from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_active_user, get_db
from app.core.rbac import require_min_role
from app.models.corrective_action import CorrectiveAction
from app.models.enums import CAStatus, SignatureMeaning, UserRole
from app.models.haccp import CCP, HaccpPlan, HaccpReview, Hazard, MonitoringRecord
from app.models.user import User
from app.schemas.haccp import (
    CCPCreate,
    CCPRead,
    CCPUpdate,
    HaccpPlanCreate,
    HaccpPlanRead,
    HaccpPlanUpdate,
    HaccpReviewCreate,
    HaccpReviewRead,
    HazardCreate,
    HazardRead,
    MonitoringRecordCreate,
    MonitoringRecordRead,
)
from app.schemas.signature import SignatureCreate
from app.services.signing import sign

router = APIRouter()


def _get_plan_or_404(db: Session, plan_id: str, company_id: str) -> HaccpPlan:
    plan = db.get(HaccpPlan, plan_id)
    if not plan or plan.company_id != company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="HACCP plan not found")
    return plan


def _get_ccp_or_404(db: Session, ccp_id: str, company_id: str) -> CCP:
    ccp = db.get(CCP, ccp_id)
    if not ccp or ccp.plan.company_id != company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CCP not found")
    return ccp


# --- HACCP Plans ---

@router.get("/plans", response_model=list[HaccpPlanRead])
def list_plans(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return db.query(HaccpPlan).filter(HaccpPlan.company_id == current_user.company_id).order_by(HaccpPlan.name).all()


@router.post("/plans", response_model=HaccpPlanRead, status_code=status.HTTP_201_CREATED)
def create_plan(
    payload: HaccpPlanCreate,
    current_user: User = Depends(require_min_role(UserRole.FOOD_SAFETY_OFFICER)),
    db: Session = Depends(get_db),
):
    plan = HaccpPlan(company_id=current_user.company_id, **payload.model_dump())
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


@router.get("/plans/{plan_id}", response_model=HaccpPlanRead)
def get_plan(plan_id: str, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return _get_plan_or_404(db, plan_id, current_user.company_id)


@router.patch("/plans/{plan_id}", response_model=HaccpPlanRead)
def update_plan(
    plan_id: str,
    payload: HaccpPlanUpdate,
    current_user: User = Depends(require_min_role(UserRole.FOOD_SAFETY_OFFICER)),
    db: Session = Depends(get_db),
):
    plan = _get_plan_or_404(db, plan_id, current_user.company_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(plan, field, value)
    db.commit()
    db.refresh(plan)
    return plan


@router.post("/plans/{plan_id}/approve", response_model=HaccpPlanRead)
def approve_plan(
    plan_id: str,
    payload: SignatureCreate,
    request: Request,
    current_user: User = Depends(require_min_role(UserRole.QA_MANAGER)),
    db: Session = Depends(get_db),
):
    plan = _get_plan_or_404(db, plan_id, current_user.company_id)
    if payload.meaning != SignatureMeaning.HACCP_PLAN_APPROVAL:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Wrong signature meaning for this action")

    content = f"haccp_plan:{plan.id}:version={plan.version}:approved_by={current_user.id}"
    sign(
        db, request=request, current_user=current_user, payload=payload,
        entity_type="haccp_plan", entity_id=plan.id, content_to_hash=content,
    )

    plan.status = "approved"
    plan.approved_by_id = current_user.id
    plan.approved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(plan)
    return plan


# --- Hazards ---

@router.get("/plans/{plan_id}/hazards", response_model=list[HazardRead])
def list_hazards(plan_id: str, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    _get_plan_or_404(db, plan_id, current_user.company_id)
    return db.query(Hazard).filter(Hazard.plan_id == plan_id).all()


@router.post("/plans/{plan_id}/hazards", response_model=HazardRead, status_code=status.HTTP_201_CREATED)
def create_hazard(
    plan_id: str,
    payload: HazardCreate,
    current_user: User = Depends(require_min_role(UserRole.FOOD_SAFETY_OFFICER)),
    db: Session = Depends(get_db),
):
    _get_plan_or_404(db, plan_id, current_user.company_id)
    hazard = Hazard(plan_id=plan_id, **payload.model_dump())
    db.add(hazard)
    db.commit()
    db.refresh(hazard)
    return hazard


# --- CCPs ---

@router.get("/plans/{plan_id}/ccps", response_model=list[CCPRead])
def list_ccps(plan_id: str, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    _get_plan_or_404(db, plan_id, current_user.company_id)
    return db.query(CCP).filter(CCP.plan_id == plan_id).order_by(CCP.number).all()


@router.post("/plans/{plan_id}/ccps", response_model=CCPRead, status_code=status.HTTP_201_CREATED)
def create_ccp(
    plan_id: str,
    payload: CCPCreate,
    current_user: User = Depends(require_min_role(UserRole.FOOD_SAFETY_OFFICER)),
    db: Session = Depends(get_db),
):
    _get_plan_or_404(db, plan_id, current_user.company_id)
    ccp = CCP(plan_id=plan_id, **payload.model_dump())
    db.add(ccp)
    db.commit()
    db.refresh(ccp)
    return ccp


@router.get("/ccps/{ccp_id}", response_model=CCPRead)
def get_ccp(ccp_id: str, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return _get_ccp_or_404(db, ccp_id, current_user.company_id)


@router.patch("/ccps/{ccp_id}", response_model=CCPRead)
def update_ccp(
    ccp_id: str,
    payload: CCPUpdate,
    current_user: User = Depends(require_min_role(UserRole.FOOD_SAFETY_OFFICER)),
    db: Session = Depends(get_db),
):
    ccp = _get_ccp_or_404(db, ccp_id, current_user.company_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(ccp, field, value)
    db.commit()
    db.refresh(ccp)
    return ccp


# --- Monitoring Records ---

@router.get("/ccps/{ccp_id}/monitoring", response_model=list[MonitoringRecordRead])
def list_monitoring_records(
    ccp_id: str, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    _get_ccp_or_404(db, ccp_id, current_user.company_id)
    return (
        db.query(MonitoringRecord)
        .filter(MonitoringRecord.ccp_id == ccp_id)
        .order_by(MonitoringRecord.recorded_at.desc())
        .limit(500)
        .all()
    )


@router.post("/ccps/{ccp_id}/monitoring", response_model=MonitoringRecordRead, status_code=status.HTTP_201_CREATED)
def record_monitoring(
    ccp_id: str,
    payload: MonitoringRecordCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    ccp = _get_ccp_or_404(db, ccp_id, current_user.company_id)

    within_limits = True
    if ccp.critical_limit_min is not None and payload.measured_value < ccp.critical_limit_min:
        within_limits = False
    if ccp.critical_limit_max is not None and payload.measured_value > ccp.critical_limit_max:
        within_limits = False

    record = MonitoringRecord(
        ccp_id=ccp_id,
        recorded_by_id=current_user.id,
        unit=payload.unit or ccp.critical_limit_unit,
        within_limits=within_limits,
        recorded_at=payload.recorded_at or datetime.now(timezone.utc),
        **payload.model_dump(exclude={"unit", "recorded_at"}),
    )
    db.add(record)
    db.flush()

    if not within_limits:
        ca = CorrectiveAction(
            company_id=current_user.company_id,
            raised_by_id=current_user.id,
            title=f"CCP deviation: {ccp.name}",
            issue_description=(
                f"Measured value {payload.measured_value} {record.unit or ''} outside critical limits "
                f"({ccp.critical_limit_min} - {ccp.critical_limit_max}) for {ccp.name}."
            ),
            source="ccp",
            source_reference_id=record.id,
            corrective_action=ccp.corrective_action_procedure,
            status=CAStatus.OPEN,
        )
        db.add(ca)
        db.flush()
        record.corrective_action_id = ca.id

    db.commit()
    db.refresh(record)
    return record


# --- Reviews (verification / validation / review history) ---

@router.get("/plans/{plan_id}/reviews", response_model=list[HaccpReviewRead])
def list_reviews(plan_id: str, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    _get_plan_or_404(db, plan_id, current_user.company_id)
    return (
        db.query(HaccpReview)
        .filter(HaccpReview.plan_id == plan_id)
        .order_by(HaccpReview.reviewed_at.desc())
        .all()
    )


@router.post("/plans/{plan_id}/reviews", response_model=HaccpReviewRead, status_code=status.HTTP_201_CREATED)
def create_review(
    plan_id: str,
    payload: HaccpReviewCreate,
    current_user: User = Depends(require_min_role(UserRole.QA_MANAGER)),
    db: Session = Depends(get_db),
):
    _get_plan_or_404(db, plan_id, current_user.company_id)
    review = HaccpReview(
        plan_id=plan_id,
        reviewed_by_id=current_user.id,
        reviewed_at=payload.reviewed_at or datetime.now(timezone.utc),
        **payload.model_dump(exclude={"reviewed_at"}),
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review
