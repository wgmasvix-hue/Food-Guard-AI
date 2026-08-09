import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_active_user, get_db
from app.core.rbac import require_min_role, require_roles
from app.models.billing import EcocashPayment, Subscription, SubscriptionPlan
from app.models.enums import EcocashPaymentStatus, SubscriptionStatus, UserRole
from app.models.user import User
from app.schemas.billing import (
    CheckoutSessionRequest,
    CheckoutSessionResponse,
    EcocashConfirmRequest,
    EcocashPaymentRead,
    EcocashRejectRequest,
    EcocashSubmitRequest,
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


@router.get("/ecocash/info")
def ecocash_info():
    """Static info the frontend needs to show payment instructions —
    no auth required, nothing sensitive."""
    return {
        "merchant_number": settings.ECOCASH_MERCHANT_NUMBER,
        "instructions": (
            f"Send the plan's price to EcoCash number {settings.ECOCASH_MERCHANT_NUMBER}, "
            "including your reference code in the payment note if EcoCash allows it. "
            "Then submit your EcoCash transaction reference below for review."
        ),
    }


@router.get("/ecocash/mine", response_model=list[EcocashPaymentRead])
def list_my_ecocash_payments(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if not current_user.company_id:
        return []
    return (
        db.query(EcocashPayment)
        .filter(EcocashPayment.company_id == current_user.company_id)
        .order_by(EcocashPayment.created_at.desc())
        .all()
    )


@router.post("/ecocash/submit", response_model=EcocashPaymentRead, status_code=status.HTTP_201_CREATED)
def submit_ecocash_payment(
    payload: EcocashSubmitRequest,
    current_user: User = Depends(require_min_role(UserRole.COMPANY_ADMIN)),
    db: Session = Depends(get_db),
):
    """Step 1: the customer says which plan they want to pay for. We hand
    back a unique reference code and payment instructions; no money has
    moved yet — that happens out of band via the EcoCash app/USSD."""
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is not assigned to a company")
    plan = (
        db.query(SubscriptionPlan)
        .filter(SubscriptionPlan.code == payload.plan_code, SubscriptionPlan.is_active.is_(True))
        .first()
    )
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    if not plan.is_self_serve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="This plan is sales-assisted — contact us to set it up."
        )

    reference_code = f"FG-{uuid.uuid4().hex[:6].upper()}"
    payment = EcocashPayment(
        company_id=current_user.company_id,
        plan_id=plan.id,
        reference_code=reference_code,
        amount_cents=plan.price_cents,
        currency=plan.currency,
        submitted_by_id=current_user.id,
        status=EcocashPaymentStatus.PENDING,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


@router.post("/ecocash/{payment_id}/confirm", response_model=EcocashPaymentRead)
def confirm_ecocash_payment(
    payment_id: str,
    payload: EcocashConfirmRequest,
    current_user: User = Depends(require_min_role(UserRole.COMPANY_ADMIN)),
    db: Session = Depends(get_db),
):
    """Step 2: the customer has actually paid and submits the EcoCash
    transaction reference they got back, moving this into the admin
    review queue."""
    payment = db.get(EcocashPayment, payment_id)
    if not payment or payment.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    if payment.status != EcocashPaymentStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This payment has already been submitted for review.")

    payment.transaction_reference = payload.transaction_reference
    payment.payer_phone = payload.payer_phone
    payment.status = EcocashPaymentStatus.SUBMITTED
    db.commit()
    db.refresh(payment)
    return payment


@router.get("/ecocash/pending", response_model=list[EcocashPaymentRead])
def list_pending_ecocash_payments(
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN)), db: Session = Depends(get_db)
):
    return (
        db.query(EcocashPayment)
        .filter(EcocashPayment.status == EcocashPaymentStatus.SUBMITTED)
        .order_by(EcocashPayment.created_at)
        .all()
    )


@router.post("/ecocash/{payment_id}/approve", response_model=EcocashPaymentRead)
def approve_ecocash_payment(
    payment_id: str,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db),
):
    payment = db.get(EcocashPayment, payment_id)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    if payment.status != EcocashPaymentStatus.SUBMITTED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This payment isn't awaiting review.")

    payment.status = EcocashPaymentStatus.APPROVED
    payment.reviewed_by_id = current_user.id
    payment.reviewed_at = datetime.now(timezone.utc)

    sub = db.query(Subscription).filter(Subscription.company_id == payment.company_id).first()
    if sub:
        sub.plan_id = payment.plan_id
        sub.status = SubscriptionStatus.ACTIVE
        sub.cancel_at_period_end = False

    db.commit()
    db.refresh(payment)
    return payment


@router.post("/ecocash/{payment_id}/reject", response_model=EcocashPaymentRead)
def reject_ecocash_payment(
    payment_id: str,
    payload: EcocashRejectRequest,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db),
):
    payment = db.get(EcocashPayment, payment_id)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    if payment.status != EcocashPaymentStatus.SUBMITTED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This payment isn't awaiting review.")

    payment.status = EcocashPaymentStatus.REJECTED
    payment.reviewed_by_id = current_user.id
    payment.reviewed_at = datetime.now(timezone.utc)
    payment.review_notes = payload.reason
    db.commit()
    db.refresh(payment)
    return payment


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
