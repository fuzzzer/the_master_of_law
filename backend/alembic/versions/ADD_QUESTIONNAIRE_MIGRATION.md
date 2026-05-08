# Alembic Migration: Add Questionnaire Models

## Manual Migration Instructions

To avoid merge conflicts with parallel agents, this migration is documented
as a manual step rather than auto-generated.

### Step 1 — Create the migration file

Run from the `backend/` directory:

```bash
cd backend
source .venv/bin/activate
alembic revision -m "add_questionnaire_models" --rev-id add_questionnaire_models_20260509
```

### Step 2 — Populate the migration

Edit the generated file and use this content for `upgrade()` and `downgrade()`:

```python
"""add_questionnaire_models

Revision ID: add_questionnaire_models_20260509
Revises: <latest_revision_id>
Create Date: 2026-05-09 02:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_questionnaire_models_20260509'
down_revision: Union[str, None] = '<REPLACE_WITH_CURRENT_HEAD>'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'questionnaire_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('question_id', sa.String(100), nullable=False),
        sa.Column('question_text_ka', sa.Text(), nullable=False),
        sa.Column('question_type', sa.String(20), nullable=False),
        sa.Column('options', postgresql.JSONB(), nullable=True),
        sa.Column('required', sa.Boolean(), default=True, nullable=False),
        sa.Column('purpose', sa.Text(), nullable=True),
        sa.Column('legal_relevance', sa.Text(), nullable=True),
        sa.Column('sort_order', sa.Integer(), default=0, nullable=False),
        sa.Column('answer_value', sa.Text(), nullable=True),
        sa.Column('skipped', sa.Boolean(), default=False, nullable=False),
        sa.Column('answered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_questionnaire_items_conversation_id', 'questionnaire_items', ['conversation_id'])


def downgrade() -> None:
    op.drop_index('ix_questionnaire_items_conversation_id', table_name='questionnaire_items')
    op.drop_table('questionnaire_items')
```

> **Note:** Replace `<REPLACE_WITH_CURRENT_HEAD>` with the actual current head revision ID from your Alembic history.

### Step 3 — Run the migration

```bash
cd backend
alembic upgrade head
```

## Model Reference

The migration creates the `questionnaire_items` table used by:
- `backend/app/models/questionnaire.py` → `QuestionnaireItem`
- `backend/app/repositories/questionnaire_repository.py` → `QuestionnaireRepository`
- `backend/app/services/questionnaire_service.py` → `QuestionnaireService`
