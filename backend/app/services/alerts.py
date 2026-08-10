"""Company-wide alerting: creates in-app Notification rows for the
relevant staff and, if a WhatsApp provider is configured (see
app.services.whatsapp), also sends a WhatsApp message to anyone with a
phone number on file. In-app notifications always happen; WhatsApp is
best-effort on top.
"""
from sqlalchemy.orm import Session

from app.models.enums import NotificationLevel, UserRole
from app.models.notification import Notification
from app.models.user import User
from app.services.whatsapp import get_whatsapp_provider

# Roles that receive compliance alerts — the people who'd actually act on
# a temperature excursion or an overdue corrective action.
ALERT_RECIPIENT_ROLES = (UserRole.COMPANY_ADMIN, UserRole.QA_MANAGER, UserRole.FOOD_SAFETY_OFFICER)


def notify_company(
    db: Session,
    *,
    company_id: str,
    level: NotificationLevel,
    title: str,
    message: str,
    link: str | None = None,
) -> None:
    """Create an in-app notification for each relevant staff member in
    the company, and best-effort send a WhatsApp message to anyone with
    a phone number on file. Does not commit — call within the caller's
    existing transaction so the alert and the event that triggered it
    (e.g. a temperature log) succeed or fail together.
    """
    recipients = (
        db.query(User)
        .filter(
            User.company_id == company_id,
            User.is_active.is_(True),
            User.role.in_(ALERT_RECIPIENT_ROLES),
        )
        .all()
    )
    provider = get_whatsapp_provider()
    for user in recipients:
        db.add(
            Notification(
                user_id=user.id,
                company_id=company_id,
                level=level,
                title=title,
                message=message,
                link=link,
            )
        )
        if user.phone:
            provider.send_message(to_phone=user.phone, body=f"*{title}*\n{message}")
