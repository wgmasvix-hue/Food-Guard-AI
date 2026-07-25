from datetime import date

from sqlalchemy import Date, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import AuditStatus, AuditType


class Audit(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "audits"

    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    facility_id: Mapped[str | None] = mapped_column(ForeignKey("facilities.id", ondelete="SET NULL"))
    lead_auditor_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    template_id: Mapped[str | None] = mapped_column(ForeignKey("audit_templates.id", ondelete="SET NULL"))

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    audit_type: Mapped[AuditType] = mapped_column(String(50), nullable=False)
    standard: Mapped[str | None] = mapped_column(String(100))  # ISO 22000, BRC, HACCP, ...
    scope: Mapped[str | None] = mapped_column(Text)
    scheduled_date: Mapped[date | None] = mapped_column(Date, index=True)
    completed_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[AuditStatus] = mapped_column(String(50), default=AuditStatus.SCHEDULED)
    score: Mapped[float | None] = mapped_column(Float)
    summary: Mapped[str | None] = mapped_column(Text)
    external_auditor: Mapped[str | None] = mapped_column(String(255))  # body/person for external audits

    lead_auditor = relationship("User")
    template = relationship("AuditTemplate")
    findings: Mapped[list["AuditFinding"]] = relationship(back_populates="audit", cascade="all, delete-orphan")
    checklist_items: Mapped[list["AuditChecklistItem"]] = relationship(
        back_populates="audit", cascade="all, delete-orphan"
    )
    ai_analyses: Mapped[list["AuditAIAnalysis"]] = relationship(
        back_populates="audit", cascade="all, delete-orphan", order_by="AuditAIAnalysis.generated_at.desc()"
    )


class AuditFinding(Base, UUIDMixin, TimestampMixin):
    """Non-conformance / observation raised during an audit (feeds CAPA)."""

    __tablename__ = "audit_findings"

    audit_id: Mapped[str] = mapped_column(ForeignKey("audits.id", ondelete="CASCADE"), index=True)
    corrective_action_id: Mapped[str | None] = mapped_column(
        ForeignKey("corrective_actions.id", ondelete="SET NULL")
    )
    clause: Mapped[str | None] = mapped_column(String(100))  # standard clause reference
    severity: Mapped[str] = mapped_column(String(20), default="minor")  # critical/major/minor/observation
    description: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="open")  # open/closed

    audit: Mapped[Audit] = relationship(back_populates="findings")
