from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_active_user, get_db
from app.core.rbac import require_min_role
from app.models.billing import Subscription, SubscriptionPlan
from app.models.enums import SubscriptionStatus, UserRole
from app.models.user import User
from app.schemas.billing import (
    CheckoutSessionRequest,
    CheckoutSessionResponse,
    PortalSessionRequest,
    PortalSessionResponse,
    SubscriptionPlanRead,
    SubscriptionRead,
)
from app.services.billing import get_billing_provider
from app.services.billing.limits import ai_credits_remaining

router = APIRouter()

_STRIPE_STATUS_MAP = {
    "active": SubscriptionStatus.ACTIVE,
    "trialing": SubscriptionStatus.TRIALING,
    "past_due": SubscriptionStatus.PAST_DUE,
    "canceled": SubscriptionStatus.CANCELED,
    "incomplete": SubscriptionStatus.INCOMPLETE,
    "incomplete_expired": SubscriptionStatus.CANCELED,
    "unpaid": SubscriptionStatus.PAST_DUE,
}


@router.get("/plans", response_model=list[SubscriptionPlanRead])
def list_plans(db: Session = Depends(get_db)):
    return (
        db.query(SubscriptionPlan)
        .filter(SubscriptionPlan.is_active.is_(True))
        .order_by(SubscriptionPlan.sort_order)
        .all()
    )


@router.get("/subscription", response_model=SubscriptionRead)
def get_my_subscription(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is not assigned to a company")
    sub = db.query(Subscription).filter(Subscription.company_id == current_user.company_id).first()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No subscription on file")
    data = SubscriptionRead.model_validate(sub)
    data.ai_credits_remaining = ai_credits_remaining(db, current_user.company_id)
    return data


@router.post("/checkout", response_model=CheckoutSessionResponse)
async def create_checkout(
    payload: CheckoutSessionRequest,
    current_user: User = Depends(require_min_role(UserRole.COMPANY_ADMIN)),
    db: Session = Depends(get_db),
):
    plan = (
        db.query(SubscriptionPlan)
        .filter(SubscriptionPlan.code == payload.plan_code, SubscriptionPlan.is_active.is_(True))
        .first()
    )
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    if not plan.is_self_serve:
        return CheckoutSessionResponse(message="This plan is sales-assisted — contact us to set it up.")
    if not plan.stripe_price_id:
        return CheckoutSessionResponse(message="This plan isn't connected to Stripe yet.")
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is not assigned to a company")

    provider = get_billing_provider()
    if not await provider.is_available():
        return CheckoutSessionResponse(
            message="Billing isn't configured on this deployment yet. Set STRIPE_SECRET_KEY to enable checkout."
        )
    url = await provider.create_checkout_session(
        customer_email=current_user.email,
        stripe_price_id=plan.stripe_price_id,
        company_id=current_user.company_id,
        success_url=payload.success_url,
        cancel_url=payload.cancel_url,
    )
    return CheckoutSessionResponse(checkout_url=url)


@router.post("/portal", response_model=PortalSessionResponse)
async def create_portal(
    payload: PortalSessionRequest,
    current_user: User = Depends(require_min_role(UserRole.COMPANY_ADMIN)),
    db: Session = Depends(get_db),
):
    sub = db.query(Subscription).filter(Subscription.company_id == current_user.company_id).first()
    if not sub or not sub.stripe_customer_id:
        return PortalSessionResponse(message="No billing account on file yet — subscribe to a paid plan first.")

    provider = get_billing_provider()
    if not await provider.is_available():
        return PortalSessionResponse(message="Billing isn't configured on this deployment yet.")
    url = await provider.create_portal_session(stripe_customer_id=sub.stripe_customer_id, return_url=payload.return_url)
    return PortalSessionResponse(portal_url=url)


@router.post("/webhook", include_in_schema=False)
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    provider = get_billing_provider()
    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")
    try:
        event = provider.verify_webhook(payload, signature)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    event_type = event["type"]
    data_object = event["data"]["object"]

    if event_type in ("customer.subscription.created", "customer.subscription.updated"):
        _sync_subscription_from_stripe(db, data_object)
    elif event_type == "customer.subscription.deleted":
        _handle_subscription_canceled(db, data_object)

    return {"status": "ok"}


def _sync_subscription_from_stripe(db: Session, stripe_sub) -> None:
    company_id = (stripe_sub.get("metadata") or {}).get("company_id")
    if not company_id:
        return
    sub = db.query(Subscription).filter(Subscription.company_id == company_id).first()
    if not sub:
        return

    items = (stripe_sub.get("items") or {}).get("data") or []
    if items:
        price_id = items[0].get("price", {}).get("id")
        if price_id:
            plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.stripe_price_id == price_id).first()
            if plan:
                sub.plan_id = plan.id

    sub.stripe_customer_id = stripe_sub.get("customer")
    sub.stripe_subscription_id = stripe_sub.get("id")
    sub.status = _STRIPE_STATUS_MAP.get(stripe_sub.get("status") or "", SubscriptionStatus.ACTIVE)
    sub.cancel_at_period_end = bool(stripe_sub.get("cancel_at_period_end"))
    period_end = stripe_sub.get("current_period_end")
    if period_end:
        sub.current_period_end = datetime.fromtimestamp(period_end, tz=timezone.utc)
    db.commit()


def _handle_subscription_canceled(db: Session, stripe_sub) -> None:
    company_id = (stripe_sub.get("metadata") or {}).get("company_id")
    if not company_id:
        return
    sub = db.query(Subscription).filter(Subscription.company_id == company_id).first()
    if not sub:
        return
    # Downgrade to Free automatically so plan-limit enforcement kicks back
    # in, rather than leaving the company stuck on a canceled paid plan.
    free_plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.code == "free").first()
    if free_plan:
        sub.plan_id = free_plan.id
    sub.status = SubscriptionStatus.ACTIVE
    sub.cancel_at_period_end = False
    db.commit()
