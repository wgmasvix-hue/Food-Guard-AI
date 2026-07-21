from datetime import date

from pydantic import BaseModel

from app.models.enums import DocumentCategory
from app.schemas.common import TimestampedORMModel


class DocumentCreate(BaseModel):
    title: str
    category: DocumentCategory = DocumentCategory.OTHER
    description: str | None = None
    expires_on: date | None = None
    facility_id: str | None = None
    supplier_id: str | None = None
    content_text: str | None = None  # for AI-generated / text documents


class DocumentVersionRead(TimestampedORMModel):
    document_id: str
    uploaded_by_id: str | None = None
    version: int
    file_path: str | None = None
    file_name: str | None = None
    content_type: str | None = None
    size_bytes: int | None = None
    content_text: str | None = None
    change_note: str | None = None


class DocumentRead(TimestampedORMModel):
    company_id: str
    facility_id: str | None = None
    owner_id: str | None = None
    supplier_id: str | None = None
    title: str
    category: DocumentCategory
    description: str | None = None
    expires_on: date | None = None
    is_archived: bool
    versions: list[DocumentVersionRead] = []
