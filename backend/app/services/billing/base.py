"""Modular billing provider interface.

Mirrors app.services.ai's AIProvider pattern: the rest of the app never
depends on the Stripe SDK directly, only on this protocol, so a
DisabledBillingProvider can stand in when no payment processor is
configured (billing UI still works, checkout just explains it isn't
wired up yet) and a different processor could replace Stripe later
without touching callers.
"""
from abc import ABC, abstractmethod
from typing import Any


class BillingProvider(ABC):
    @abstractmethod
    async def create_checkout_session(
        self, *, customer_email: str, stripe_price_id: str, company_id: str, success_url: str, cancel_url: str
    ) -> str | None:
        """Return a checkout URL to redirect the user to, or None if unavailable."""
        raise NotImplementedError

    @abstractmethod
    async def create_portal_session(self, *, stripe_customer_id: str, return_url: str) -> str | None:
        """Return a billing-management portal URL, or None if unavailable."""
        raise NotImplementedError

    @abstractmethod
    def verify_webhook(self, payload: bytes, signature: str) -> Any:
        """Verify and parse a webhook payload. Raises if the signature is invalid."""
        raise NotImplementedError

    @abstractmethod
    async def is_available(self) -> bool:
        """Whether real payment processing is configured."""
        raise NotImplementedError
