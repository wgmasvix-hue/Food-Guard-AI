from datetime import date, datetime

from pydantic import BaseModel

from app.models.enums import CCPStatus, HazardType
from app.schemas.common import TimestampedORMModel


class HaccpPlanCreate(BaseModel):
    facility_id: str | None = None
    product_id: str | None = None
    name: str
    scope: str | None = None
    process_description: str | None = None


class HaccpPlanUpdate(BaseModel):
    name: str | None = None
    scope: str | None = None
    process_description: str | None = None
    status: str | None = None
    next_review_date: date | None = None


class HaccpPlanRead(TimestampedORMModel):
    company_id: str
    facility_id: str | None = None
    product_id: str | None = None
    name: str
    scope: str | None = None
    process_description: str | None = None
    version: int
    status: str
    next_review_date: date | None = None


class HazardCreate(BaseModel):
    process_step: str
    hazard_type: HazardType
    description: str
    likelihood: int = 1
    severity: int = 1
    control_measures: str | None = None
    is_ccp: bool = False
    justification: str | None = None


class HazardRead(TimestampedORMModel):
    plan_id: str
    process_step: str
    hazard_type: HazardType
    description: str
    likelihood: int
    severity: int
    control_measures: str | None = None
    is_ccp: bool
    justification: str | None = None
    risk_score: int


class CCPCreate(BaseModel):
    hazard_id: str | None = None
    number: str
    name: str
    process_step: str | None = None
    critical_limit_min: float | None = None
    critical_limit_max: float | None = None
    critical_limit_unit: str | None = None
    critical_limit_description: str | None = None
    monitoring_procedure: str | None = None
    monitoring_frequency: str | None = None
    corrective_action_procedure: str | None = None
    verification_procedure: str | None = None
    validation_notes: str | None = None
    responsible_role: str | None = None


class CCPUpdate(BaseModel):
    name: str | None = None
    critical_limit_min: float | None = None
    critical_limit_max: float | None = None
    critical_limit_unit: str | None = None
    critical_limit_description: str | None = None
    monitoring_procedure: str | None = None
    monitoring_frequency: str | None = None
    corrective_action_procedure: str | None = None
    verification_procedure: str | None = None
    validation_notes: str | None = None
    responsible_role: str | None = None
    status: CCPStatus | None = None


class CCPRead(TimestampedORMModel):
    plan_id: str
    hazard_id: str | None = None
    number: str
    name: str
    process_step: str | None = None
    critical_limit_min: float | None = None
    critical_limit_max: float | None = None
    critical_limit_unit: str | None = None
    critical_limit_description: str | None = None
    monitoring_procedure: str | None = None
    monitoring_frequency: str | None = None
    corrective_action_procedure: str | None = None
    verification_procedure: str | None = None
    validation_notes: str | None = None
    responsible_role: str | None = None
    status: CCPStatus


class MonitoringRecordCreate(BaseModel):
    batch_id: str | None = None
    measured_value: float
    unit: str | None = None
    notes: str | None = None
    recorded_at: datetime | None = None


class MonitoringRecordRead(TimestampedORMModel):
    ccp_id: str
    batch_id: str | None = None
    recorded_by_id: str | None = None
    measured_value: float
    unit: str | None = None
    within_limits: bool
    notes: str | None = None
    recorded_at: datetime
    corrective_action_id: str | None = None


class HaccpReviewCreate(BaseModel):
    review_type: str = "periodic"
    summary: str
    outcome: str = "no_change"
    reviewed_at: datetime | None = None


class HaccpReviewRead(TimestampedORMModel):
    plan_id: str
    reviewed_by_id: str | None = None
    review_type: str
    summary: str
    outcome: str
    reviewed_at: datetime
