from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import ChecklistStatus, GMPCategory


class ChecklistTemplate(Base, UUIDMixin, TimestampMixin):
    """Reusable GMP inspection form definition."""

    __tablename__ = "checklist_templates"

    company_id: Mapped[str | None] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[GMPCategory] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    frequency: Mapped[str | None] = mapped_column(String(50))  # daily/weekly/monthly
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    items: Mapped[list["ChecklistTemplateItem"]] = relationship(
        back_populates="template", cascade="all, delete-orphan", order_by="ChecklistTemplateItem.order"
    )


class ChecklistTemplateItem(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "checklist_template_items"

    template_id: Mapped[str] = mapped_column(ForeignKey("checklist_templates.id", ondelete="CASCADE"), index=True)
    order: Mapped[int] = mapped_column(Integer, default=0)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    guidance: Mapped[str | None] = mapped_column(Text)
    is_critical: Mapped[bool] = mapped_column(Boolean, default=False)

    template: Mapped[ChecklistTemplate] = relationship(back_populates="items")


class Checklist(Base, UUIDMixin, TimestampMixin):
    """A completed (or in-progress) inspection based on a template."""

    __tablename__ = "checklists"

    template_id: Mapped[str] = mapped_column(ForeignKey("checklist_templates.id", ondelete="CASCADE"), index=True)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    facility_id: Mapped[str | None] = mapped_column(ForeignKey("facilities.id", ondelete="SET NULL"))
    inspector_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    status: Mapped[ChecklistStatus] = mapped_column(String(50), default=ChecklistStatus.IN_PROGRESS)
    score: Mapped[float | None] = mapped_column(Float)  # % of passed items
    notes: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    template: Mapped[ChecklistTemplate] = relationship()
    inspector = relationship("User")
    items: Mapped[list["ChecklistItem"]] = relationship(back_populates="checklist", cascade="all, delete-orphan")


class ChecklistItem(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "checklist_items"

    checklist_id: Mapped[str] = mapped_column(ForeignKey("checklists.id", ondelete="CASCADE"), index=True)
    template_item_id: Mapped[str | None] = mapped_column(
        ForeignKey("checklist_template_items.id", ondelete="SET NULL")
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    is_critical: Mapped[bool] = mapped_column(Boolean, default=False)
    result: Mapped[str | None] = mapped_column(String(20))  # pass/fail/na
    comment: Mapped[str | None] = mapped_column(Text)
    photo_path: Mapped[str | None] = mapped_column(String(500))
    corrective_action_id: Mapped[str | None] = mapped_column(
        ForeignKey("corrective_actions.id", ondelete="SET NULL")
    )

    checklist: Mapped[Checklist] = relationship(back_populates="items")
