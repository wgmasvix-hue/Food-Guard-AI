from typing import Any

import stripe

from app.core.config import settings
from app.services.billing.base import BillingProvider


class StripeBillingProvider(BillingProvider):
    """Talks to Stripe. Only instantiated when STRIPE_SECRET_KEY is set."""

    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY

    async def create_checkout_session(
        self, *, customer_email: str, stripe_price_id: str, company_id: str, success_url: str, cancel_url: str
    ) -> str | None:
        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": stripe_price_id, "quantity": 1}],
            customer_email=customer_email,
            success_url=success_url,
            cancel_url=cancel_url,
            client_reference_id=company_id,
            metadata={"company_id": company_id},
            subscription_data={"metadata": {"company_id": company_id}},
        )
        return session.url

    async def create_portal_session(self, *, stripe_customer_id: str, return_url: str) -> str | None:
        session = stripe.billing_portal.Session.create(customer=stripe_customer_id, return_url=return_url)
        return session.url

    def verify_webhook(self, payload: bytes, signature: str) -> Any:
        return stripe.Webhook.construct_event(payload, signature, settings.STRIPE_WEBHOOK_SECRET)

    async def is_available(self) -> bool:
        return bool(settings.STRIPE_SECRET_KEY)
