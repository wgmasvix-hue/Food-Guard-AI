import logging
import re

import httpx

from app.core.config import settings
from app.services.whatsapp.base import WhatsAppProvider

logger = logging.getLogger(__name__)

TWILIO_API_URL = "https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"


def _to_whatsapp_address(phone: str) -> str:
    """Twilio wants "whatsapp:+<E.164 number>". Accepts either a bare
    number or one already prefixed, strips anything but digits/+."""
    phone = phone.strip()
    if phone.startswith("whatsapp:"):
        return phone
    digits = re.sub(r"[^\d+]", "", phone)
    if not digits.startswith("+"):
        digits = f"+{digits}"
    return f"whatsapp:{digits}"


class TwilioWhatsAppProvider(WhatsAppProvider):
    """Sends WhatsApp messages via Twilio's WhatsApp API. Delivery
    failures are logged and swallowed (return False) — alerts are
    best-effort, a bad phone number shouldn't break the request that
    triggered the alert (e.g. recording a temperature reading)."""

    def send_message(self, *, to_phone: str, body: str) -> bool:
        if not to_phone:
            return False
        url = TWILIO_API_URL.format(account_sid=settings.TWILIO_ACCOUNT_SID)
        data = {
            "From": settings.TWILIO_WHATSAPP_FROM,
            "To": _to_whatsapp_address(to_phone),
            "Body": body,
        }
        try:
            resp = httpx.post(
                url, data=data, auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN), timeout=10.0
            )
            if resp.status_code >= 400:
                logger.warning("WhatsApp send failed (%s): %s", resp.status_code, resp.text[:500])
                return False
            return True
        except httpx.HTTPError:
            logger.warning("WhatsApp send failed (network error)", exc_info=True)
            return False

    def is_available(self) -> bool:
        return True
