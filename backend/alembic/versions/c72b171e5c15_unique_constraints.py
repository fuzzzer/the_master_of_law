"""unique constraints

Revision ID: c72b171e5c15
Revises: 
Create Date: 2026-06-20 20:34:50.965779

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c72b171e5c15'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check existing tables to make migration conditional and idempotent
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'conversations' not in existing_tables:
        op.create_table('conversations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.String(length=128), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('phase', sa.String(length=20), nullable=False),
        sa.Column('legal_domain', sa.String(length=100), nullable=True),
        sa.Column('case_ready', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_conversations_user_id'), 'conversations', ['user_id'], unique=False)

    if 'users' not in existing_tables:
        op.create_table('users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('firebase_uid', sa.String(length=128), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('display_name', sa.String(length=255), nullable=True),
        sa.Column('photo_url', sa.String(length=500), nullable=True),
        sa.Column('tier', sa.String(length=10), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_users_firebase_uid'), 'users', ['firebase_uid'], unique=True)

    if 'case_files' not in existing_tables:
        op.create_table('case_files',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('conversation_id', sa.UUID(), nullable=True),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('facts', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('evidence', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('applicable_laws', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('defense_strategies', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('prosecution_args', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('action_checklist', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('unclear_items', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('lawyer_brief', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('citations', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('retrieved_chunks', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('rendered_text', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('user_notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_case_files_user_id'), 'case_files', ['user_id'], unique=False)

    if 'credit_transactions' not in existing_tables:
        op.create_table('credit_transactions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('transaction_type', sa.String(length=20), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_credit_transactions_user_id'), 'credit_transactions', ['user_id'], unique=False)

    if 'feedback' not in existing_tables:
        op.create_table('feedback',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('target_type', sa.String(length=20), nullable=False),
        sa.Column('target_id', sa.UUID(), nullable=False),
        sa.Column('reviewer_id', sa.UUID(), nullable=True),
        sa.Column('reviewer_type', sa.String(length=20), nullable=False),
        sa.Column('category', sa.String(length=30), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('specific_section', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['reviewer_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_feedback_category'), 'feedback', ['category'], unique=False)
        op.create_index(op.f('ix_feedback_target_id'), 'feedback', ['target_id'], unique=False)

    if 'messages' not in existing_tables:
        op.create_table('messages',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('conversation_id', sa.UUID(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('citations', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('retrieved_chunk_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('credit_cost', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_messages_conversation_id'), 'messages', ['conversation_id'], unique=False)

    if 'questionnaire_answers' not in existing_tables:
        op.create_table('questionnaire_answers',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('conversation_id', sa.UUID(), nullable=False),
        sa.Column('question_id', sa.String(length=64), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('answer_value', sa.Text(), nullable=True),
        sa.Column('answer_type', sa.String(length=20), nullable=False),
        sa.Column('skipped', sa.Boolean(), nullable=False),
        sa.Column('answered_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_questionnaire_answers_conversation_id'), 'questionnaire_answers', ['conversation_id'], unique=False)

    if 'questionnaire_questions' not in existing_tables:
        op.create_table('questionnaire_questions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('conversation_id', sa.UUID(), nullable=False),
        sa.Column('question_id', sa.String(length=64), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('question_type', sa.String(length=20), nullable=False),
        sa.Column('options', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('required', sa.Boolean(), nullable=False),
        sa.Column('purpose', sa.Text(), nullable=True),
        sa.Column('legal_relevance', sa.Text(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_questionnaire_questions_conversation_id'), 'questionnaire_questions', ['conversation_id'], unique=False)

    if 'user_credits' not in existing_tables:
        op.create_table('user_credits',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('tier', sa.String(length=10), nullable=False),
        sa.Column('credit_balance', sa.Integer(), nullable=False),
        sa.Column('daily_credits_used', sa.Integer(), nullable=False),
        sa.Column('daily_reset_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_user_credits_user_id'), 'user_credits', ['user_id'], unique=True)

    # ── Safe De-duplication ──────────────────────────────
    # For user_credits: keep the latest update (by updated_at, break tie with id)
    op.execute("""
        DELETE FROM user_credits a USING user_credits b 
        WHERE (a.updated_at < b.updated_at OR (a.updated_at = b.updated_at AND a.id < b.id)) 
          AND a.user_id = b.user_id
    """)

    # For questionnaire_answers: keep the latest answered (by answered_at, break tie with id)
    op.execute("""
        DELETE FROM questionnaire_answers a USING questionnaire_answers b
        WHERE (a.answered_at < b.answered_at OR (a.answered_at = b.answered_at AND a.id < b.id)) 
          AND a.conversation_id = b.conversation_id 
          AND a.question_id = b.question_id
    """)

    # ── Ensure constraints are present ────────────────────
    # For user_credits: make ix_user_credits_user_id unique index
    op.execute("DROP INDEX IF EXISTS ix_user_credits_user_id")
    op.create_index('ix_user_credits_user_id', 'user_credits', ['user_id'], unique=True)

    # For questionnaire_answers: add uq_conv_question_answer constraint if not exists
    # We drop if it exists to be safe and avoid errors, then recreate
    op.execute("ALTER TABLE questionnaire_answers DROP CONSTRAINT IF EXISTS uq_conv_question_answer")
    op.create_unique_constraint('uq_conv_question_answer', 'questionnaire_answers', ['conversation_id', 'question_id'])


def downgrade() -> None:
    op.drop_constraint('uq_conv_question_answer', 'questionnaire_answers', type_='unique')
    op.drop_index(op.f('ix_user_credits_user_id'), table_name='user_credits')
    op.create_index('ix_user_credits_user_id', 'user_credits', ['user_id'], unique=False)
