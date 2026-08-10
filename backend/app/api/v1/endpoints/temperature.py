from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_active_user, get_db
from app.core.rbac import require_min_role
from app.models.corrective_action import CorrectiveAction
from app.models.enums import CAStatus, NotificationLevel, UserRole
from app.models.temperature import TemperatureLog, TemperatureUnit
from app.models.user import User
from app.schemas.temperature import (
    TemperatureLogCreate,
    TemperatureLogRead,
    TemperatureUnitCreate,
    TemperatureUnitRead,
    TemperatureUnitUpdate,
)
from app.services.alerts import notify_company

router = APIRouter()


def _get_unit_or_404(db: Session, unit_id: str, company_id: str) -> TemperatureUnit:
    unit = db.get(TemperatureUnit, unit_id)
    if not unit or unit.company_id != company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Temperature unit not found")
    return unit


@router.get("/units", response_model=list[TemperatureUnitRead])
def list_units(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return (
        db.query(TemperatureUnit)
        .filter(TemperatureUnit.company_id == current_user.company_id)
        .order_by(TemperatureUnit.name)
        .all()
    )


@router.post("/units", response_model=TemperatureUnitRead, status_code=status.HTTP_201_CREATED)
def create_unit(
    payload: TemperatureUnitCreate,
    current_user: User = Depends(require_min_role(UserRole.PRODUCTION_SUPERVISOR)),
    db: Session = Depends(get_db),
):
    unit = TemperatureUnit(company_id=current_user.company_id, **payload.model_dump())
    db.add(unit)
    db.commit()
    db.refresh(unit)
    return unit


@router.patch("/units/{unit_id}", response_model=TemperatureUnitRead)
def update_unit(
    unit_id: str,
    payload: TemperatureUnitUpdate,
    current_user: User = Depends(require_min_role(UserRole.PRODUCTION_SUPERVISOR)),
    db: Session = Depends(get_db),
):
    unit = _get_unit_or_404(db, unit_id, current_user.company_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(unit, field, value)
    db.commit()
    db.refresh(unit)
    return unit


@router.get("/units/{unit_id}/logs", response_model=list[TemperatureLogRead])
def list_logs(unit_id: str, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    _get_unit_or_404(db, unit_id, current_user.company_id)
    return (
        db.query(TemperatureLog)
        .filter(TemperatureLog.unit_id == unit_id)
        .order_by(TemperatureLog.recorded_at.desc())
        .limit(500)
        .all()
    )


@router.post("/units/{unit_id}/logs", response_model=TemperatureLogRead, status_code=status.HTTP_201_CREATED)
def record_log(
    unit_id: str,
    payload: TemperatureLogCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    unit = _get_unit_or_404(db, unit_id, current_user.company_id)

    within_limits = True
    if unit.min_temp is not None and payload.temperature < unit.min_temp:
        within_limits = False
    if unit.max_temp is not None and payload.temperature > unit.max_temp:
        within_limits = False

    log = TemperatureLog(
        unit_id=unit_id,
        recorded_by_id=current_user.id,
        within_limits=within_limits,
        recorded_at=payload.recorded_at or datetime.now(timezone.utc),
        **payload.model_dump(exclude={"recorded_at"}),
    )
    db.add(log)
    db.flush()

    if not within_limits:
        ca = CorrectiveAction(
            company_id=current_user.company_id,
            facility_id=unit.facility_id,
            raised_by_id=current_user.id,
            title=f"Temperature alert: {unit.name}",
            issue_description=(
                f"Recorded {payload.temperature}°C outside limits "
                f"({unit.min_temp}°C - {unit.max_temp}°C) for {unit.name}."
            ),
            source="temperature",
            source_reference_id=log.id,
            status=CAStatus.OPEN,
        )
        db.add(ca)
        db.flush()
        log.corrective_action_id = ca.id

        notify_company(
            db,
            company_id=current_user.company_id,
            level=NotificationLevel.CRITICAL,
            title=f"Temperature alert: {unit.name}",
            message=(
                f"{payload.temperature}°C recorded, outside limits "
                f"({unit.min_temp}°C–{unit.max_temp}°C). Corrective action opened automatically."
            ),
            link="/temperature",
        )

    db.commit()
    db.refresh(log)
    return log


@router.get("/alerts", response_model=list[TemperatureLogRead])
def list_alerts(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """Recent out-of-limit readings across all units for the company."""
    return (
        db.query(TemperatureLog)
        .join(TemperatureUnit, TemperatureLog.unit_id == TemperatureUnit.id)
        .filter(TemperatureUnit.company_id == current_user.company_id, TemperatureLog.within_limits.is_(False))
        .order_by(TemperatureLog.recorded_at.desc())
        .limit(100)
        .all()
    )
