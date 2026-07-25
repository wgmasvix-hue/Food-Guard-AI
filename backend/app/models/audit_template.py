from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import RiskLevel


class AuditTemplate(Base, UUIDMixin, TimestampMixin):
    """Reusable audit question set (mirrors ChecklistTemplate for GMP)."""

    __tablename__ = "audit_templates"

    company_id: Mapped[str | None] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    standard: Mapped[str | None] = mapped_column(String(100))  # ISO 22000, BRCGS, HACCP...
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    items: Mapped[list["AuditTemplateItem"]] = relationship(
        back_populates="template", cascade="all, delete-orphan", order_by="AuditTemplateItem.order"
    )


class AuditTemplateItem(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "audit_template_items"

    template_id: Mapped[str] = mapped_column(ForeignKey("audit_templates.id", ondelete="CASCADE"), index=True)
    order: Mapped[int] = mapped_column(Integer, default=0)
    clause: Mapped[str | None] = mapped_column(String(100))
    question: Mapped[str] = mapped_column(Text, nullable=False)
    guidance: Mapped[str | None] = mapped_column(Text)
    is_critical: Mapped[bool] = mapped_column(Boolean, default=False)

    template: Mapped[AuditTemplate] = relationship(back_populates="items")


class AuditChecklistItem(Base, UUIDMixin, TimestampMixin):
    """A single answered question within an audit, generated from an
    AuditTemplateItem when the audit was created from a template."""

    __tablename__ = "audit_checklist_items"

    audit_id: Mapped[str] = mapped_column(ForeignKey("audits.id", ondelete="CASCADE"), index=True)
    template_item_id: Mapped[str | None] = mapped_column(ForeignKey("audit_template_items.id", ondelete="SET NULL"))
    clause: Mapped[str | None] = mapped_column(String(100))
    question: Mapped[str] = mapped_column(Text, nullable=False)
    is_critical: Mapped[bool] = mapped_column(Boolean, default=False)
    result: Mapped[str | None] = mapped_column(String(20))  # pass/fail/na
    comment: Mapped[str | None] = mapped_column(Text)
    corrective_action_id: Mapped[str | None] = mapped_column(
        ForeignKey("corrective_actions.id", ondelete="SET NULL")
    )

    audit = relationship("Audit", back_populates="checklist_items")


class AuditAIAnalysis(Base, UUIDMixin, TimestampMixin):
    """AI-generated analysis of a completed audit: summary, risk, root cause,
    recommended corrective actions, and an improvement plan. An audit can be
    re-analyzed (e.g. after more findings are added); newest row wins."""

    __tablename__ = "audit_ai_analyses"

    audit_id: Mapped[str] = mapped_column(ForeignKey("audits.id", ondelete="CASCADE"), index=True)
    generated_by_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    risk_level: Mapped[RiskLevel] = mapped_column(String(20), default=RiskLevel.MEDIUM)
    root_cause_analysis: Mapped[str | None] = mapped_column(Text)
    recommended_corrective_actions: Mapped[str | None] = mapped_column(Text)
    improvement_plan: Mapped[str | None] = mapped_column(Text)
    model: Mapped[str | None] = mapped_column(String(100))
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    audit = relationship("Audit", back_populates="ai_analyses")
    generated_by = relationship("User")
