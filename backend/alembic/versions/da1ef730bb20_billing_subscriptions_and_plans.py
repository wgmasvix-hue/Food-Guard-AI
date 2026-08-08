"""billing subscriptions and plans

Revision ID: da1ef730bb20
Revises: f96dbb32b6ce
Create Date: 2026-08-08 21:21:09.539011

"""
import uuid
from datetime import datetime, timezone
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column


# revision identifiers, used by Alembic.
revision: str = 'da1ef730bb20'
down_revision: Union[str, None] = 'f96dbb32b6ce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Default tiers. Adjust price_cents/limits/stripe_price_id to match your
# actual Stripe products before relying on self-serve checkout — these are
# starting-point defaults, not fixed business decisions baked into the code.
PLAN_DEFAULTS = [
    {
        "code": "free",
        "name": "Free",
        "price_cents": 0,
        "currency": "usd",
        "billing_interval": "none",
        "max_facilities": 1,
        "max_employees": 10,
        "ai_assistant_included": False,
        "is_self_serve": True,
        "stripe_price_id": None,
        "sort_order": 0,
        "is_active": True,
    },
    {
        "code": "pro",
        "name": "Pro",
        "price_cents": 9900,
        "currency": "usd",
        "billing_interval": "month",
        "max_facilities": 5,
        "max_employees": 100,
        "ai_assistant_included": True,
        "is_self_serve": True,
        "stripe_price_id": None,
        "sort_order": 1,
        "is_active": True,
    },
    {
        "code": "enterprise",
        "name": "Enterprise",
        "price_cents": 0,
        "currency": "usd",
        "billing_interval": "none",
        "max_facilities": None,
        "max_employees": None,
        "ai_assistant_included": True,
        "is_self_serve": False,
        "stripe_price_id": None,
        "sort_order": 2,
        "is_active": True,
    },
]


def upgrade() -> None:
    now = datetime.now(timezone.utc)

    op.create_table(
        'subscription_plans',
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('price_cents', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False),
        sa.Column('billing_interval', sa.String(length=20), nullable=False),
        sa.Column('max_facilities', sa.Integer(), nullable=True),
        sa.Column('max_employees', sa.Integer(), nullable=True),
        sa.Column('ai_assistant_included', sa.Boolean(), nullable=False),
        sa.Column('is_self_serve', sa.Boolean(), nullable=False),
        sa.Column('stripe_price_id', sa.String(length=255), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
    )

    op.create_table(
        'subscriptions',
        sa.Column('company_id', sa.String(length=36), nullable=False),
        sa.Column('plan_id', sa.String(length=36), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False),
        sa.Column('stripe_customer_id', sa.String(length=255), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(length=255), nullable=True),
        sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancel_at_period_end', sa.Boolean(), nullable=False),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['plan_id'], ['subscription_plans.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_subscriptions_company_id'), 'subscriptions', ['company_id'], unique=True)

    # --- seed the default plans ---
    plans_table = table(
        'subscription_plans',
        column('id', sa.String),
        column('code', sa.String),
        column('name', sa.String),
        column('price_cents', sa.Integer),
        column('currency', sa.String),
        column('billing_interval', sa.String),
        column('max_facilities', sa.Integer),
        column('max_employees', sa.Integer),
        column('ai_assistant_included', sa.Boolean),
        column('is_self_serve', sa.Boolean),
        column('stripe_price_id', sa.String),
        column('sort_order', sa.Integer),
        column('is_active', sa.Boolean),
        column('created_at', sa.DateTime),
        column('updated_at', sa.DateTime),
    )
    plan_ids = {}
    rows = []
    for plan in PLAN_DEFAULTS:
        plan_id = str(uuid.uuid4())
        plan_ids[plan["code"]] = plan_id
        rows.append({**plan, "id": plan_id, "created_at": now, "updated_at": now})
    op.bulk_insert(plans_table, rows)

    # --- backfill a Free subscription for every company that predates this migration ---
    connection = op.get_bind()
    free_plan_id = plan_ids["free"]
    existing_company_ids = [row[0] for row in connection.execute(sa.text("SELECT id FROM companies"))]
    if existing_company_ids:
        subscriptions_table = table(
            'subscriptions',
            column('id', sa.String),
            column('company_id', sa.String),
            column('plan_id', sa.String),
            column('status', sa.String),
            column('cancel_at_period_end', sa.Boolean),
            column('created_at', sa.DateTime),
            column('updated_at', sa.DateTime),
        )
        op.bulk_insert(
            subscriptions_table,
            [
                {
                    "id": str(uuid.uuid4()),
                    "company_id": company_id,
                    "plan_id": free_plan_id,
                    "status": "active",
                    "cancel_at_period_end": False,
                    "created_at": now,
                    "updated_at": now,
                }
                for company_id in existing_company_ids
            ],
        )


def downgrade() -> None:
    op.drop_index(op.f('ix_subscriptions_company_id'), table_name='subscriptions')
    op.drop_table('subscriptions')
    op.drop_table('subscription_plans')
