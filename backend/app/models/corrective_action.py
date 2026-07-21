from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import CAStatus


class CorrectiveAction(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "corrective_actions"

    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    facility_id: Mapped[str | None] = mapped_column(ForeignKey("facilities.id", ondelete="SET NULL"))
    raised_by_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    responsible_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    verified_by_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    issue_description: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str | None] = mapped_column(String(50))  # gmp/ccp/temperature/audit/complaint/other
    source_reference_id: Mapped[str | None] = mapped_column(String(36))  # id of originating record
    root_cause: Mapped[str | None] = mapped_column(Text)
    corrective_action: Mapped[str | None] = mapped_column(Text)
    preventive_action: Mapped[str | None] = mapped_column(Text)
    deadline: Mapped[date | None] = mapped_column(Date)
    evidence_photo_path: Mapped[str | None] = mapped_column(String(500))
    verification_notes: Mapped[str | None] = mapped_column(Text)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[CAStatus] = mapped_column(String(50), default=CAStatus.OPEN, index=True)

    raised_by = relationship("User", foreign_keys=[raised_by_id])
    responsible = relationship("User", foreign_keys=[responsible_id])
    verified_by = relationship("User", foreign_keys=[verified_by_id])
