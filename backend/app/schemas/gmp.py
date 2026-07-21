from datetime import datetime

from pydantic import BaseModel

from app.models.enums import ChecklistStatus, GMPCategory
from app.schemas.common import TimestampedORMModel


class ChecklistTemplateItemCreate(BaseModel):
    order: int = 0
    question: str
    guidance: str | None = None
    is_critical: bool = False


class ChecklistTemplateItemRead(TimestampedORMModel):
    template_id: str
    order: int
    question: str
    guidance: str | None = None
    is_critical: bool


class ChecklistTemplateCreate(BaseModel):
    name: str
    category: GMPCategory
    description: str | None = None
    frequency: str | None = None
    items: list[ChecklistTemplateItemCreate] = []


class ChecklistTemplateRead(TimestampedORMModel):
    company_id: str | None = None
    name: str
    category: GMPCategory
    description: str | None = None
    frequency: str | None = None
    is_active: bool
    items: list[ChecklistTemplateItemRead] = []


class ChecklistStart(BaseModel):
    template_id: str
    facility_id: str | None = None


class ChecklistItemSubmit(BaseModel):
    id: str
    result: str  # pass/fail/na
    comment: str | None = None
    photo_path: str | None = None


class ChecklistSubmit(BaseModel):
    items: list[ChecklistItemSubmit]
    notes: str | None = None


class ChecklistItemRead(TimestampedORMModel):
    checklist_id: str
    template_item_id: str | None = None
    question: str
    is_critical: bool
    result: str | None = None
    comment: str | None = None
    photo_path: str | None = None
    corrective_action_id: str | None = None


class ChecklistRead(TimestampedORMModel):
    template_id: str
    company_id: str
    facility_id: str | None = None
    inspector_id: str | None = None
    status: ChecklistStatus
    score: float | None = None
    notes: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    items: list[ChecklistItemRead] = []
