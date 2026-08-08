from typing import Any

from app.services.billing.base import BillingProvider


class DisabledBillingProvider(BillingProvider):
    """No-op provider used when no Stripe keys are configured. The billing
    UI (plans, current subscription) still works fully — only real
    checkout/portal/webhook processing is unavailable."""

    async def create_checkout_session(self, **kwargs) -> str | None:
        return None

    async def create_portal_session(self, **kwargs) -> str | None:
        return None

    def verify_webhook(self, payload: bytes, signature: str) -> Any:
        raise RuntimeError("Billing is not configured. Set STRIPE_SECRET_KEY and STRIPE_WEBHOOK_SECRET.")

    async def is_available(self) -> bool:
        return False
