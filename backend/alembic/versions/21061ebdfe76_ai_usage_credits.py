"""ai usage credits

Revision ID: 21061ebdfe76
Revises: da1ef730bb20
Create Date: 2026-08-09 06:22:21.752344

"""
from datetime import datetime, timezone
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '21061ebdfe76'
down_revision: Union[str, None] = 'da1ef730bb20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# None = unlimited. Free gets a monthly cap so accounts get real AI usage
# without a paid plan; adjust freely — this is a starting-point default,
# not a fixed business decision baked into the code.
CREDITS_BY_PLAN_CODE = {
    "free": 20,
    "pro": None,
    "enterprise": None,
}


def upgrade() -> None:
    op.add_column('subscription_plans', sa.Column('ai_credits_per_month', sa.Integer(), nullable=True))
    op.add_column(
        'subscriptions',
        sa.Column('ai_credits_used', sa.Integer(), nullable=False, server_default='0'),
    )
    op.add_column('subscriptions', sa.Column('ai_credits_reset_at', sa.DateTime(timezone=True), nullable=True))

    connection = op.get_bind()
    for code, credits in CREDITS_BY_PLAN_CODE.items():
        connection.execute(
            sa.text("UPDATE subscription_plans SET ai_credits_per_month = :credits WHERE code = :code"),
            {"credits": credits, "code": code},
        )
    connection.execute(
        sa.text("UPDATE subscriptions SET ai_credits_reset_at = :now WHERE ai_credits_reset_at IS NULL"),
        {"now": datetime.now(timezone.utc)},
    )


def downgrade() -> None:
    op.drop_column('subscriptions', 'ai_credits_reset_at')
    op.drop_column('subscriptions', 'ai_credits_used')
    op.drop_column('subscription_plans', 'ai_credits_per_month')
