from datetime import date, timedelta

from app.core.config import settings
from app.models.corrective_action import CorrectiveAction
from app.models.notification import Notification
from app.models.user import User
from app.services.overdue_alerts import check_and_alert_overdue_corrective_actions
from app.services.whatsapp.disabled_provider import DisabledWhatsAppProvider
from app.services.whatsapp.factory import get_whatsapp_provider


def test_factory_returns_disabled_provider_when_unconfigured():
    get_whatsapp_provider.cache_clear()
    original = (settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN, settings.TWILIO_WHATSAPP_FROM)
    settings.TWILIO_ACCOUNT_SID = ""
    settings.TWILIO_AUTH_TOKEN = ""
    settings.TWILIO_WHATSAPP_FROM = ""
    try:
        provider = get_whatsapp_provider()
        assert isinstance(provider, DisabledWhatsAppProvider)
        assert provider.is_available() is False
        assert provider.send_message(to_phone="+263771234567", body="test") is False
    finally:
        settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN, settings.TWILIO_WHATSAPP_FROM = original
        get_whatsapp_provider.cache_clear()


def test_factory_returns_twilio_provider_when_configured():
    get_whatsapp_provider.cache_clear()
    original = (settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN, settings.TWILIO_WHATSAPP_FROM)
    settings.TWILIO_ACCOUNT_SID = "ACxxxx"
    settings.TWILIO_AUTH_TOKEN = "secret"
    settings.TWILIO_WHATSAPP_FROM = "whatsapp:+14155238886"
    try:
        from app.services.whatsapp.twilio_provider import TwilioWhatsAppProvider

        provider = get_whatsapp_provider()
        assert isinstance(provider, TwilioWhatsAppProvider)
        assert provider.is_available() is True
    finally:
        settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN, settings.TWILIO_WHATSAPP_FROM = original
        get_whatsapp_provider.cache_clear()


def _make_overdue_ca(db_session, company_id, title="Fix the thing"):
    ca = CorrectiveAction(
        company_id=company_id,
        title=title,
        issue_description="Something went wrong",
        status="open",
        deadline=date.today() - timedelta(days=3),
    )
    db_session.add(ca)
    db_session.commit()
    db_session.refresh(ca)
    return ca


def test_overdue_check_marks_status_and_notifies(auth_client, db_session):
    admin = db_session.query(User).filter(User.email == "owner@acme-foods.com").first()
    ca = _make_overdue_ca(db_session, admin.company_id)

    count = check_and_alert_overdue_corrective_actions(db_session)
    assert count == 1

    db_session.refresh(ca)
    assert ca.status == "overdue"

    notifications = db_session.query(Notification).filter(Notification.user_id == admin.id).all()
    assert len(notifications) == 1
    assert "overdue" in notifications[0].title.lower()


def test_overdue_check_is_idempotent(auth_client, db_session):
    admin = db_session.query(User).filter(User.email == "owner@acme-foods.com").first()
    _make_overdue_ca(db_session, admin.company_id)

    first_count = check_and_alert_overdue_corrective_actions(db_session)
    second_count = check_and_alert_overdue_corrective_actions(db_session)

    assert first_count == 1
    assert second_count == 0

    notifications = db_session.query(Notification).filter(Notification.user_id == admin.id).all()
    assert len(notifications) == 1


def test_overdue_check_ignores_cas_with_no_deadline_or_future_deadline(auth_client, db_session):
    admin = db_session.query(User).filter(User.email == "owner@acme-foods.com").first()
    db_session.add(
        CorrectiveAction(
            company_id=admin.company_id, title="No deadline", issue_description="x", status="open", deadline=None
        )
    )
    db_session.add(
        CorrectiveAction(
            company_id=admin.company_id,
            title="Future deadline",
            issue_description="x",
            status="open",
            deadline=date.today() + timedelta(days=5),
        )
    )
    db_session.commit()

    count = check_and_alert_overdue_corrective_actions(db_session)
    assert count == 0
