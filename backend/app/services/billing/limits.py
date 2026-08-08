"""Plan-based usage limits, enforced at the point of creation."""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.billing import Subscription, SubscriptionPlan
from app.models.company import Facility
from app.models.employee import Employee


def _current_plan(db: Session, company_id: str) -> SubscriptionPlan | None:
    sub = db.query(Subscription).filter(Subscription.company_id == company_id).first()
    if not sub or not sub.is_usable:
        return None
    return sub.plan


def enforce_facility_limit(db: Session, company_id: str) -> None:
    plan = _current_plan(db, company_id)
    if not plan or plan.max_facilities is None:
        return
    count = db.query(Facility).filter(Facility.company_id == company_id).count()
    if count >= plan.max_facilities:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Your {plan.name} plan allows up to {plan.max_facilities} "
            f"facilit{'y' if plan.max_facilities == 1 else 'ies'}. Upgrade to add more.",
        )


def enforce_employee_limit(db: Session, company_id: str) -> None:
    plan = _current_plan(db, company_id)
    if not plan or plan.max_employees is None:
        return
    count = db.query(Employee).filter(Employee.company_id == company_id).count()
    if count >= plan.max_employees:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Your {plan.name} plan allows up to {plan.max_employees} employees. Upgrade to add more.",
        )


def ai_assistant_allowed(db: Session, company_id: str | None) -> bool:
    if not company_id:
        return True  # e.g. a Super Admin with no company — nothing to gate
    plan = _current_plan(db, company_id)
    if not plan:
        return True  # no subscription row at all — fail open rather than block unexpectedly
    return plan.ai_assistant_included
