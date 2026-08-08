from functools import lru_cache

from app.core.config import settings
from app.services.billing.base import BillingProvider
from app.services.billing.disabled_provider import DisabledBillingProvider


@lru_cache
def get_billing_provider() -> BillingProvider:
    if settings.STRIPE_SECRET_KEY:
        from app.services.billing.stripe_provider import StripeBillingProvider

        return StripeBillingProvider()
    return DisabledBillingProvider()
