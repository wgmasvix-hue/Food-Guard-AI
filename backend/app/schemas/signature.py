from datetime import datetime

from pydantic import BaseModel

from app.models.enums import SignatureMeaning
from app.schemas.common import TimestampedORMModel


class SignatureCreate(BaseModel):
    entity_type: str
    entity_id: str
    meaning: SignatureMeaning
    typed_name: str
    notes: str | None = None


class SignatureRead(TimestampedORMModel):
    entity_type: str
    entity_id: str
    meaning: SignatureMeaning
    signed_by_id: str
    typed_name: str
    ip_address: str | None = None
    signed_at: datetime
    notes: str | None = None
