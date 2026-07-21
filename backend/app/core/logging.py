"""Persist security-relevant actions to the system_logs table."""
from sqlalchemy.orm import Session

from app.models.system_log import SystemLog


def log_action(
    db: Session,
    *,
    user_id: str | None,
    action: str,
    entity: str | None = None,
    entity_id: str | None = None,
    detail: str | None = None,
    ip_address: str | None = None,
    company_id: str | None = None,
) -> None:
    entry = SystemLog(
        user_id=user_id,
        company_id=company_id,
        action=action,
        entity=entity,
        entity_id=entity_id,
        detail=detail,
        ip_address=ip_address,
    )
    db.add(entry)
    db.commit()
