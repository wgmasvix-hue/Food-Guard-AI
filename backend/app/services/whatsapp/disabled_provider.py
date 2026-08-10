import logging

from app.services.whatsapp.base import WhatsAppProvider

logger = logging.getLogger(__name__)


class DisabledWhatsAppProvider(WhatsAppProvider):
    """No-op provider used when no WhatsApp credentials are configured.
    Alerts still get created as in-app Notification rows — this just
    means they don't also go out over WhatsApp."""

    def send_message(self, *, to_phone: str, body: str) -> bool:
        logger.info("WhatsApp not configured — skipping message to %s", to_phone)
        return False

    def is_available(self) -> bool:
        return False
