"""pipeline traces

Revision ID: d41f8a2b9c03
Revises: c72b171e5c15
Create Date: 2026-07-19 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd41f8a2b9c03'
down_revision: Union[str, None] = 'c72b171e5c15'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'pipeline_traces' not in existing_tables:
        op.create_table('pipeline_traces',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('conversation_id', sa.String(length=64), nullable=True),
        sa.Column('user_id', sa.String(length=128), nullable=True),
        sa.Column('entry_point', sa.String(length=30), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('user_message', sa.Text(), nullable=False),
        sa.Column('response_text', sa.Text(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('steps', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_pipeline_traces_conversation_id'), 'pipeline_traces', ['conversation_id'], unique=False)
        op.create_index(op.f('ix_pipeline_traces_user_id'), 'pipeline_traces', ['user_id'], unique=False)
        op.create_index(op.f('ix_pipeline_traces_created_at'), 'pipeline_traces', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_pipeline_traces_created_at'), table_name='pipeline_traces')
    op.drop_index(op.f('ix_pipeline_traces_user_id'), table_name='pipeline_traces')
    op.drop_index(op.f('ix_pipeline_traces_conversation_id'), table_name='pipeline_traces')
    op.drop_table('pipeline_traces')
