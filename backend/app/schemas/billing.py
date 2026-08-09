from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import TimestampedORMModel


class SubscriptionPlanRead(TimestampedORMModel):
    code: str
    name: str
    price_cents: int
    currency: str
    billing_interval: str
    max_facilities: int | None
    max_employees: int | None
    ai_assistant_included: bool
    ai_credits_per_month: int | None
    is_self_serve: bool
    sort_order: int


class SubscriptionRead(TimestampedORMModel):
    company_id: str
    plan_id: str
    status: str
    current_period_end: datetime | None
    cancel_at_period_end: bool
    plan: SubscriptionPlanRead
    ai_credits_remaining: int | None = None  # None = unlimited; computed, not a DB column


class CheckoutSessionRequest(BaseModel):
    plan_code: str
    success_url: str
    cancel_url: str


class CheckoutSessionResponse(BaseModel):
    checkout_url: str | None = None
    message: str | None = None  # set when checkout isn't available (stub provider, non-self-serve plan, etc.)


class PortalSessionRequest(BaseModel):
    return_url: str


class PortalSessionResponse(BaseModel):
    portal_url: str | None = None
    message: str | None = None
