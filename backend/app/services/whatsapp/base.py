"""Modular WhatsApp provider interface.

Mirrors app.services.ai/app.services.billing's provider pattern: the
rest of the app never depends on a specific WhatsApp API directly, only
on this protocol, so a DisabledWhatsAppProvider stands in when no
provider is configured — alerts just don't go out over WhatsApp (they
still land as in-app Notification rows), nothing breaks.

Synchronous by design (not async like AIProvider/BillingProvider):
callers are the sync request-handling code paths that raise alerts
(e.g. recording a temperature reading), and a WhatsApp send is a single
best-effort HTTP call, not worth threading async through those call
sites for.
"""
from abc import ABC, abstractmethod


class WhatsAppProvider(ABC):
    @abstractmethod
    def send_message(self, *, to_phone: str, body: str) -> bool:
        """Send a WhatsApp message. Returns True if the provider accepted
        it for delivery, False otherwise (never raises for a delivery
        failure — callers treat WhatsApp as best-effort)."""
        raise NotImplementedError

    @abstractmethod
    def is_available(self) -> bool:
        """Whether a real WhatsApp provider is configured."""
        raise NotImplementedError
