"""Plan-based usage limits, enforced at the point of creation/use."""
from datetime import datetime, timezone

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


def _current_subscription(db: Session, company_id: str) -> Subscription | None:
    sub = db.query(Subscription).filter(Subscription.company_id == company_id).first()
    if not sub or not sub.is_usable:
        return None
    return sub


def _is_new_period(sub: Subscription) -> bool:
    now = datetime.now(timezone.utc)
    reset_at = sub.ai_credits_reset_at
    return reset_at is None or (reset_at.year, reset_at.month) != (now.year, now.month)


def _effective_credits_used(sub: Subscription) -> int:
    """Credits used so far in the *current* calendar month — 0 if the
    persisted counter is from an earlier month and hasn't been reset yet
    (the reset itself is applied lazily, only when a credit is next
    consumed, so this stays a read-only computation)."""
    return 0 if _is_new_period(sub) else sub.ai_credits_used


def check_ai_credits(db: Session, company_id: str | None) -> None:
    """Raises 402 if the company is out of AI credits for this period.
    Read-only — call before attempting an AI call, then call
    consume_ai_credit() after a successful response so failed calls don't
    cost a credit."""
    if not company_id:
        return
    sub = _current_subscription(db, company_id)
    if not sub:
        return  # no usable subscription on file — fail open rather than block unexpectedly
    plan = sub.plan
    if plan.ai_credits_per_month is None:
        return  # unlimited
    if _effective_credits_used(sub) >= plan.ai_credits_per_month:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"You've used all {plan.ai_credits_per_month} free AI credits this month on the "
            f"{plan.name} plan. Upgrade for unlimited access, or wait until next month.",
        )


def consume_ai_credit(db: Session, company_id: str | None) -> None:
    """Records one unit of AI usage. Call only after a successful AI
    response — a failed/unavailable AI call shouldn't cost a credit."""
    if not company_id:
        return
    sub = _current_subscription(db, company_id)
    if not sub or sub.plan.ai_credits_per_month is None:
        return
    if _is_new_period(sub):
        sub.ai_credits_used = 0
        sub.ai_credits_reset_at = datetime.now(timezone.utc)
    sub.ai_credits_used += 1
    db.commit()


def ai_credits_remaining(db: Session, company_id: str | None) -> int | None:
    """None = unlimited; otherwise credits left this period (never negative)."""
    if not company_id:
        return None
    sub = _current_subscription(db, company_id)
    if not sub or sub.plan.ai_credits_per_month is None:
        return None
    return max(0, sub.plan.ai_credits_per_month - _effective_credits_used(sub))
