from pydantic import BaseModel

from app.schemas.common import TimestampedORMModel


class AIGenerateRequest(BaseModel):
    document_type: str  # haccp_plan | sop | cleaning_procedure | policy | training_material |
                         # audit_report | risk_assessment | corrective_action | supplier_evaluation
    prompt: str
    save_as_document: bool = False
    document_title: str | None = None


class AIGenerateResponse(BaseModel):
    content: str
    document_id: str | None = None


class AIChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None


class AIMessageRead(TimestampedORMModel):
    conversation_id: str
    role: str
    content: str
    model: str | None = None


class AIConversationRead(TimestampedORMModel):
    user_id: str
    title: str
    messages: list[AIMessageRead] = []
