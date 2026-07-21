from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class Supplier(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "suppliers"

    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_name: Mapped[str | None] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    address: Mapped[str | None] = mapped_column(Text)
    approval_status: Mapped[str] = mapped_column(String(50), default="pending")  # pending/approved/rejected/suspended
    certification: Mapped[str | None] = mapped_column(String(255))  # e.g. BRC, FSSC 22000
    certification_expires_on: Mapped[date | None] = mapped_column(Date)
    risk_rating: Mapped[str | None] = mapped_column(String(20))  # low/medium/high
    notes: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    company = relationship("Company")
