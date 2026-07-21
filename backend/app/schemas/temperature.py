from datetime import datetime

from pydantic import BaseModel

from app.models.enums import TemperatureUnitType
from app.schemas.common import TimestampedORMModel


class TemperatureUnitCreate(BaseModel):
    facility_id: str | None = None
    name: str
    unit_type: TemperatureUnitType
    min_temp: float | None = None
    max_temp: float | None = None
    location: str | None = None


class TemperatureUnitUpdate(BaseModel):
    name: str | None = None
    min_temp: float | None = None
    max_temp: float | None = None
    location: str | None = None
    is_active: bool | None = None


class TemperatureUnitRead(TimestampedORMModel):
    company_id: str
    facility_id: str | None = None
    name: str
    unit_type: TemperatureUnitType
    min_temp: float | None = None
    max_temp: float | None = None
    location: str | None = None
    is_active: bool


class TemperatureLogCreate(BaseModel):
    temperature: float
    notes: str | None = None
    recorded_at: datetime | None = None


class TemperatureLogRead(TimestampedORMModel):
    unit_id: str
    recorded_by_id: str | None = None
    temperature: float
    within_limits: bool
    notes: str | None = None
    recorded_at: datetime
    corrective_action_id: str | None = None
