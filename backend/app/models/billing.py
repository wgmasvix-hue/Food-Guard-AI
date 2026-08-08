"""Subscription billing: plan definitions and each company's current subscription.

Payment processing itself is abstracted behind app.services.billing (mirrors
app.services.ai's provider pattern) so this schema doesn't assume Stripe
specifically, even though Stripe is the only real implementation today.
"""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import SubscriptionStatus


class SubscriptionPlan(Base, UUIDMixin, TimestampMixin):
    """A billing tier definition (Free / Pro / Enterprise). Reference data,
    seeded by migration — not created through the API."""

    __tablename__ = "subscription_plans"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)  # free | pro | enterprise
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    price_cents: Mapped[int] = mapped_column(Integer, default=0)  # per billing_interval; 0 = free or "contact us"
    currency: Mapped[str] = mapped_column(String(10), default="usd")
    billing_interval: Mapped[str] = mapped_column(String(20), default="month")  # month | year | none
    max_facilities: Mapped[int | None] = mapped_column(Integer)  # None = unlimited
    max_employees: Mapped[int | None] = mapped_column(Integer)
    ai_assistant_included: Mapped[bool] = mapped_column(Boolean, default=False)
    is_self_serve: Mapped[bool] = mapped_column(Boolean, default=True)  # False = sales-assisted ("Contact us")
    stripe_price_id: Mapped[str | None] = mapped_column(String(255))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="plan")


class Subscription(Base, UUIDMixin, TimestampMixin):
    """A company's current billing subscription. One per company."""

    __tablename__ = "subscriptions"

    company_id: Mapped[str] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )
    plan_id: Mapped[str] = mapped_column(ForeignKey("subscription_plans.id", ondelete="RESTRICT"), nullable=False)
    status: Mapped[SubscriptionStatus] = mapped_column(String(30), default=SubscriptionStatus.ACTIVE)
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255))
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(255))
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False)

    company = relationship("Company", backref="subscription", uselist=False)
    plan: Mapped[SubscriptionPlan] = relationship(back_populates="subscriptions")

    @property
    def is_usable(self) -> bool:
        """Whether the company should currently get plan features — active/
        trialing subscriptions do, even if cancel_at_period_end is set (they
        keep access until the period actually ends)."""
        return self.status in (SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING)
