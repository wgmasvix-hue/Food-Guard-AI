from app.schemas.common import TimestampedORMModel


class AttachmentRead(TimestampedORMModel):
    entity_type: str
    entity_id: str
    uploaded_by_id: str | None = None
    file_path: str
    file_name: str | None = None
    content_type: str | None = None
    size_bytes: int | None = None
    caption: str | None = None
