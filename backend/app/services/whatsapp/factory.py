from functools import lru_cache

from app.core.config import settings
from app.services.whatsapp.base import WhatsAppProvider
from app.services.whatsapp.disabled_provider import DisabledWhatsAppProvider


@lru_cache
def get_whatsapp_provider() -> WhatsAppProvider:
    if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN and settings.TWILIO_WHATSAPP_FROM:
        from app.services.whatsapp.twilio_provider import TwilioWhatsAppProvider

        return TwilioWhatsAppProvider()
    return DisabledWhatsAppProvider()
