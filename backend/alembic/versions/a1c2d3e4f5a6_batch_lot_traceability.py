"""batch lot traceability

Revision ID: a1c2d3e4f5a6
Revises: 06a37faeff8a
Create Date: 2026-08-10 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1c2d3e4f5a6'
down_revision: Union[str, None] = '06a37faeff8a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('batches', sa.Column('recall_reason', sa.Text(), nullable=True))

    op.create_table(
        'raw_material_lots',
        sa.Column('company_id', sa.String(length=36), nullable=False),
        sa.Column('supplier_id', sa.String(length=36), nullable=True),
        sa.Column('material_name', sa.String(length=255), nullable=False),
        sa.Column('lot_number', sa.String(length=100), nullable=False),
        sa.Column('received_date', sa.Date(), nullable=True),
        sa.Column('expiry_date', sa.Date(), nullable=True),
        sa.Column('quantity_received', sa.Float(), nullable=True),
        sa.Column('unit', sa.String(length=20), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_raw_material_lots_company_id'), 'raw_material_lots', ['company_id'], unique=False)
    op.create_index(op.f('ix_raw_material_lots_lot_number'), 'raw_material_lots', ['lot_number'], unique=False)

    op.create_table(
        'batch_lot_usages',
        sa.Column('batch_id', sa.String(length=36), nullable=False),
        sa.Column('raw_material_lot_id', sa.String(length=36), nullable=False),
        sa.Column('quantity_used', sa.Float(), nullable=True),
        sa.Column('unit', sa.String(length=20), nullable=True),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['batch_id'], ['batches.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['raw_material_lot_id'], ['raw_material_lots.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_batch_lot_usages_batch_id'), 'batch_lot_usages', ['batch_id'], unique=False)
    op.create_index(
        op.f('ix_batch_lot_usages_raw_material_lot_id'), 'batch_lot_usages', ['raw_material_lot_id'], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_batch_lot_usages_raw_material_lot_id'), table_name='batch_lot_usages')
    op.drop_index(op.f('ix_batch_lot_usages_batch_id'), table_name='batch_lot_usages')
    op.drop_table('batch_lot_usages')
    op.drop_index(op.f('ix_raw_material_lots_lot_number'), table_name='raw_material_lots')
    op.drop_index(op.f('ix_raw_material_lots_company_id'), table_name='raw_material_lots')
    op.drop_table('raw_material_lots')
    op.drop_column('batches', 'recall_reason')
