from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import CCPStatus, HazardType


class HaccpPlan(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "haccp_plans"

    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    facility_id: Mapped[str | None] = mapped_column(ForeignKey("facilities.id", ondelete="SET NULL"))
    product_id: Mapped[str | None] = mapped_column(ForeignKey("products.id", ondelete="SET NULL"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    scope: Mapped[str | None] = mapped_column(Text)
    process_description: Mapped[str | None] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(50), default="draft")  # draft/approved/archived
    approved_by_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_review_date: Mapped[date | None] = mapped_column(Date)

    hazards: Mapped[list["Hazard"]] = relationship(back_populates="plan", cascade="all, delete-orphan")
    ccps: Mapped[list["CCP"]] = relationship(back_populates="plan", cascade="all, delete-orphan")
    reviews: Mapped[list["HaccpReview"]] = relationship(back_populates="plan", cascade="all, delete-orphan")


class Hazard(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "hazards"

    plan_id: Mapped[str] = mapped_column(ForeignKey("haccp_plans.id", ondelete="CASCADE"), index=True)
    process_step: Mapped[str] = mapped_column(String(255), nullable=False)
    hazard_type: Mapped[HazardType] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    likelihood: Mapped[int] = mapped_column(Integer, default=1)  # 1-5
    severity: Mapped[int] = mapped_column(Integer, default=1)    # 1-5
    control_measures: Mapped[str | None] = mapped_column(Text)
    is_ccp: Mapped[bool] = mapped_column(Boolean, default=False)
    justification: Mapped[str | None] = mapped_column(Text)  # decision-tree rationale

    plan: Mapped[HaccpPlan] = relationship(back_populates="hazards")

    @property
    def risk_score(self) -> int:
        return self.likelihood * self.severity


class CCP(Base, UUIDMixin, TimestampMixin):
    """Critical Control Point with critical limits and monitoring procedure."""

    __tablename__ = "ccps"

    plan_id: Mapped[str] = mapped_column(ForeignKey("haccp_plans.id", ondelete="CASCADE"), index=True)
    hazard_id: Mapped[str | None] = mapped_column(ForeignKey("hazards.id", ondelete="SET NULL"))
    number: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g. "CCP-1"
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    process_step: Mapped[str | None] = mapped_column(String(255))
    critical_limit_min: Mapped[float | None] = mapped_column(Float)
    critical_limit_max: Mapped[float | None] = mapped_column(Float)
    critical_limit_unit: Mapped[str | None] = mapped_column(String(50))  # °C, pH, ppm, aw...
    critical_limit_description: Mapped[str | None] = mapped_column(Text)
    monitoring_procedure: Mapped[str | None] = mapped_column(Text)
    monitoring_frequency: Mapped[str | None] = mapped_column(String(255))  # e.g. "every 2 hours"
    corrective_action_procedure: Mapped[str | None] = mapped_column(Text)
    verification_procedure: Mapped[str | None] = mapped_column(Text)
    validation_notes: Mapped[str | None] = mapped_column(Text)
    responsible_role: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[CCPStatus] = mapped_column(String(50), default=CCPStatus.ACTIVE)

    plan: Mapped[HaccpPlan] = relationship(back_populates="ccps")
    hazard = relationship("Hazard")
    monitoring_records: Mapped[list["MonitoringRecord"]] = relationship(
        back_populates="ccp", cascade="all, delete-orphan"
    )


class MonitoringRecord(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "monitoring_records"

    ccp_id: Mapped[str] = mapped_column(ForeignKey("ccps.id", ondelete="CASCADE"), index=True)
    batch_id: Mapped[str | None] = mapped_column(ForeignKey("batches.id", ondelete="SET NULL"))
    recorded_by_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    measured_value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str | None] = mapped_column(String(50))
    within_limits: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str | None] = mapped_column(Text)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    corrective_action_id: Mapped[str | None] = mapped_column(
        ForeignKey("corrective_actions.id", ondelete="SET NULL")
    )

    ccp: Mapped[CCP] = relationship(back_populates="monitoring_records")
    recorded_by = relationship("User")


class HaccpReview(Base, UUIDMixin, TimestampMixin):
    """Periodic verification / validation / review history of a HACCP plan."""

    __tablename__ = "haccp_reviews"

    plan_id: Mapped[str] = mapped_column(ForeignKey("haccp_plans.id", ondelete="CASCADE"), index=True)
    reviewed_by_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    review_type: Mapped[str] = mapped_column(String(50), default="periodic")  # periodic/verification/validation/change
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    outcome: Mapped[str] = mapped_column(String(50), default="no_change")  # no_change/updated/major_revision
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    plan: Mapped[HaccpPlan] = relationship(back_populates="reviews")
    reviewed_by = relationship("User")
