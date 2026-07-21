from datetime import date

from pydantic import BaseModel

from app.models.enums import AuditStatus, AuditType
from app.schemas.common import TimestampedORMModel


class AuditFindingCreate(BaseModel):
    clause: str | None = None
    severity: str = "minor"
    description: str
    evidence: str | None = None


class AuditFindingRead(TimestampedORMModel):
    audit_id: str
    corrective_action_id: str | None = None
    clause: str | None = None
    severity: str
    description: str
    evidence: str | None = None
    status: str


class AuditCreate(BaseModel):
    facility_id: str | None = None
    lead_auditor_id: str | None = None
    title: str
    audit_type: AuditType
    standard: str | None = None
    scope: str | None = None
    scheduled_date: date | None = None
    external_auditor: str | None = None


class AuditUpdate(BaseModel):
    title: str | None = None
    scheduled_date: date | None = None
    completed_date: date | None = None
    status: AuditStatus | None = None
    score: float | None = None
    summary: str | None = None


class AuditRead(TimestampedORMModel):
    company_id: str
    facility_id: str | None = None
    lead_auditor_id: str | None = None
    title: str
    audit_type: AuditType
    standard: str | None = None
    scope: str | None = None
    scheduled_date: date | None = None
    completed_date: date | None = None
    status: AuditStatus
    score: float | None = None
    summary: str | None = None
    external_auditor: str | None = None
    findings: list[AuditFindingRead] = []
