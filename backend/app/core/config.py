"""Application settings loaded from environment variables (.env supported)."""
from functools import lru_cache

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

INSECURE_DEFAULT_SECRET_KEY = "dev-secret-key-change-me"
KNOWN_PLACEHOLDER_SECRET_KEYS = {
    INSECURE_DEFAULT_SECRET_KEY,
    "change-me-to-a-long-random-string",
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    PROJECT_NAME: str = "FoodOS"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"

    SECRET_KEY: str = INSECURE_DEFAULT_SECRET_KEY
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 60

    DATABASE_URL: str = "postgresql+psycopg://foodguard:foodguard-dev-password@localhost:5432/foodguard"

    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost"]

    RATE_LIMIT_PER_MINUTE: int = 120
    AUTH_RATE_LIMIT_PER_MINUTE: int = 10

    AI_PROVIDER: str = "ollama"  # "ollama" | "disabled"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"
    AI_TIMEOUT_SECONDS: int = 240

    UPLOAD_DIR: str = "/data/uploads"
    MAX_UPLOAD_SIZE_MB: int = 25

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAILS_FROM: str = "noreply@foodguard.ai"

    # Billing is optional: with these unset, the billing UI still shows
    # plans/current subscription, but checkout/portal/webhooks are
    # disabled (see app.services.billing).
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    # EcoCash: manually-reconciled mobile money payments (no API integration
    # exists for this) — customers pay this number out of band, then submit
    # a transaction reference for a Super Admin to approve. See
    # app.api.v1.endpoints.billing's /ecocash/* routes.
    ECOCASH_MERCHANT_NUMBER: str = "0784457922"

    # WhatsApp alerts are optional: with these unset, alerts (overdue
    # corrective actions, temperature excursions) still land as in-app
    # Notification rows, they just don't also go out over WhatsApp. Uses
    # Twilio's WhatsApp API — see app.services.whatsapp and
    # docs/INSTALL.md "WhatsApp alerts".
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_WHATSAPP_FROM: str = ""  # e.g. "whatsapp:+14155238886"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def _use_psycopg_driver(cls, v):
        # Managed Postgres providers (Render, Heroku, etc.) hand back a plain
        # postgres:// or postgresql:// connection string. SQLAlchemy needs the
        # +psycopg suffix to pick the psycopg3 driver we actually install
        # (requirements.txt has psycopg[binary], not psycopg2) — rewrite the
        # scheme rather than requiring every deploy target to know that.
        if isinstance(v, str):
            if v.startswith("postgres://"):
                return "postgresql+psycopg://" + v[len("postgres://"):]
            if v.startswith("postgresql://"):
                return "postgresql+psycopg://" + v[len("postgresql://"):]
        return v

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def _split_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    @model_validator(mode="after")
    def _refuse_insecure_production_secret(self):
        if self.ENVIRONMENT == "production" and self.SECRET_KEY in KNOWN_PLACEHOLDER_SECRET_KEYS:
            raise RuntimeError(
                "SECRET_KEY is still set to a placeholder value while ENVIRONMENT=production. "
                "Set a unique SECRET_KEY (e.g. `openssl rand -hex 32`) in your .env before starting."
            )
        return self

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
