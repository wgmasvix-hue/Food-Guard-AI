from datetime import date, datetime

from pydantic import BaseModel

from app.models.enums import CAStatus
from app.schemas.common import TimestampedORMModel


class CorrectiveActionCreate(BaseModel):
    facility_id: str | None = None
    responsible_id: str | None = None
    title: str
    issue_description: str
    source: str | None = None
    source_reference_id: str | None = None
    root_cause: str | None = None
    corrective_action: str | None = None
    preventive_action: str | None = None
    deadline: date | None = None
    evidence_photo_path: str | None = None


class CorrectiveActionUpdate(BaseModel):
    title: str | None = None
    responsible_id: str | None = None
    root_cause: str | None = None
    corrective_action: str | None = None
    preventive_action: str | None = None
    deadline: date | None = None
    evidence_photo_path: str | None = None
    status: CAStatus | None = None


class CorrectiveActionVerify(BaseModel):
    verification_notes: str
    typed_name: str


class CorrectiveActionRead(TimestampedORMModel):
    company_id: str
    facility_id: str | None = None
    raised_by_id: str | None = None
    responsible_id: str | None = None
    verified_by_id: str | None = None
    title: str
    issue_description: str
    source: str | None = None
    source_reference_id: str | None = None
    root_cause: str | None = None
    corrective_action: str | None = None
    preventive_action: str | None = None
    deadline: date | None = None
    evidence_photo_path: str | None = None
    verification_notes: str | None = None
    verified_at: datetime | None = None
    closed_at: datetime | None = None
    status: CAStatus
