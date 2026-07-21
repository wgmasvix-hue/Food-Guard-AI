from datetime import datetime

from app.models.enums import NotificationLevel
from app.schemas.common import TimestampedORMModel


class NotificationRead(TimestampedORMModel):
    user_id: str
    level: NotificationLevel
    title: str
    message: str
    link: str | None = None
    is_read: bool
    read_at: datetime | None = None
