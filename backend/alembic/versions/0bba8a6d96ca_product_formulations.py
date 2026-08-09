"""product formulations

Revision ID: 0bba8a6d96ca
Revises: 21061ebdfe76
Create Date: 2026-08-09 06:28:34.348931

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0bba8a6d96ca'
down_revision: Union[str, None] = '21061ebdfe76'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'product_formulations',
        sa.Column('product_id', sa.String(length=36), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('batch_size', sa.Float(), nullable=True),
        sa.Column('batch_size_unit', sa.String(length=20), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by_id', sa.String(length=36), nullable=True),
        sa.Column('approved_by_id', sa.String(length=36), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['approved_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_product_formulations_product_id'), 'product_formulations', ['product_id'], unique=False
    )

    op.create_table(
        'formulation_items',
        sa.Column('formulation_id', sa.String(length=36), nullable=False),
        sa.Column('supplier_id', sa.String(length=36), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('percentage', sa.Float(), nullable=True),
        sa.Column('quantity', sa.Float(), nullable=True),
        sa.Column('unit', sa.String(length=20), nullable=True),
        sa.Column('unit_cost', sa.Float(), nullable=True),
        sa.Column('is_allergen', sa.Boolean(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['formulation_id'], ['product_formulations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_formulation_items_formulation_id'), 'formulation_items', ['formulation_id'], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_formulation_items_formulation_id'), table_name='formulation_items')
    op.drop_table('formulation_items')
    op.drop_index(op.f('ix_product_formulations_product_id'), table_name='product_formulations')
    op.drop_table('product_formulations')
