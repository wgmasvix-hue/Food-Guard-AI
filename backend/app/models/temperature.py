from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import TemperatureUnitType


class TemperatureUnit(Base, UUIDMixin, TimestampMixin):
    """A monitored location or process: cold room, freezer, cooking step, ..."""

    __tablename__ = "temperature_units"

    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    facility_id: Mapped[str | None] = mapped_column(ForeignKey("facilities.id", ondelete="SET NULL"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    unit_type: Mapped[TemperatureUnitType] = mapped_column(String(50), nullable=False)
    min_temp: Mapped[float | None] = mapped_column(Float)  # °C lower limit
    max_temp: Mapped[float | None] = mapped_column(Float)  # °C upper limit
    location: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    logs: Mapped[list["TemperatureLog"]] = relationship(back_populates="unit", cascade="all, delete-orphan")


class TemperatureLog(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "temperature_logs"

    unit_id: Mapped[str] = mapped_column(ForeignKey("temperature_units.id", ondelete="CASCADE"), index=True)
    recorded_by_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    temperature: Mapped[float] = mapped_column(Float, nullable=False)  # °C
    within_limits: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str | None] = mapped_column(Text)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    corrective_action_id: Mapped[str | None] = mapped_column(
        ForeignKey("corrective_actions.id", ondelete="SET NULL")
    )

    unit: Mapped[TemperatureUnit] = relationship(back_populates="logs")
    recorded_by = relationship("User")
