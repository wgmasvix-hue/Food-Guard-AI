from datetime import date, datetime

from pydantic import BaseModel

from app.models.enums import AuditStatus, AuditType, RiskLevel
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


class AuditTemplateItemCreate(BaseModel):
    order: int = 0
    clause: str | None = None
    question: str
    guidance: str | None = None
    is_critical: bool = False


class AuditTemplateItemRead(TimestampedORMModel):
    template_id: str
    order: int
    clause: str | None = None
    question: str
    guidance: str | None = None
    is_critical: bool


class AuditTemplateCreate(BaseModel):
    name: str
    standard: str | None = None
    description: str | None = None
    items: list[AuditTemplateItemCreate] = []


class AuditTemplateRead(TimestampedORMModel):
    company_id: str | None = None
    name: str
    standard: str | None = None
    description: str | None = None
    is_active: bool
    items: list[AuditTemplateItemRead] = []


class AuditChecklistItemSubmit(BaseModel):
    id: str
    result: str  # pass/fail/na
    comment: str | None = None


class AuditChecklistItemRead(TimestampedORMModel):
    audit_id: str
    template_item_id: str | None = None
    clause: str | None = None
    question: str
    is_critical: bool
    result: str | None = None
    comment: str | None = None
    corrective_action_id: str | None = None


class AuditCreate(BaseModel):
    facility_id: str | None = None
    lead_auditor_id: str | None = None
    template_id: str | None = None
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
    template_id: str | None = None
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
    checklist_items: list[AuditChecklistItemRead] = []


class AuditAIAnalysisRead(TimestampedORMModel):
    audit_id: str
    generated_by_id: str | None = None
    summary: str
    risk_level: RiskLevel
    root_cause_analysis: str | None = None
    recommended_corrective_actions: str | None = None
    improvement_plan: str | None = None
    model: str | None = None
    generated_at: datetime
