"""quiz_system_v2_simplified

Revision ID: 77a97650c4f7
Revises: 005
Create Date: 2025-11-02 22:36:49.166240

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '77a97650c4f7'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop old complex quiz tables
    op.execute('DROP TABLE IF EXISTS style_assignment_feedback CASCADE')
    op.execute('DROP TABLE IF EXISTS feature_correlation CASCADE')
    op.execute('DROP TABLE IF EXISTS feature_learning_data CASCADE')
    op.execute('DROP TABLE IF EXISTS quiz_response_items CASCADE')
    op.execute('DROP TABLE IF EXISTS quiz_responses CASCADE')
    op.execute('DROP TABLE IF EXISTS quiz_clothing_items CASCADE')
    op.execute('DROP TABLE IF EXISTS style_categories CASCADE')
    
    # Create new simplified style_categories table
    op.create_table(
        'style_categories',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('gender', sa.String(10), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('ai_theme_prompt', sa.Text, nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('name', 'gender', name='unique_category_per_gender')
    )
    op.create_index('ix_style_categories_gender', 'style_categories', ['gender'])
    
    # Create new quiz_items table
    op.create_table(
        'quiz_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('image_url', sa.String(500), nullable=False),
        sa.Column('question_type', sa.String(50), nullable=False),  # pants, shirt, shorts, overlayer, shoes
        sa.Column('style_category', sa.String(100), nullable=False),  # Bohemian, Classic, etc.
        sa.Column('gender', sa.String(10), nullable=False),
        sa.Column('display_order', sa.Integer, nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()'))
    )
    op.create_index('ix_quiz_items_gender', 'quiz_items', ['gender'])
    op.create_index('ix_quiz_items_question_type', 'quiz_items', ['question_type'])
    op.create_index('ix_quiz_items_style_category', 'quiz_items', ['style_category'])
    
    # Create new quiz_responses table
    op.create_table(
        'quiz_responses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('gender', sa.String(10), nullable=False),
        sa.Column('selected_items', postgresql.JSONB, nullable=False),  # {pants: uuid, shirt: uuid, ...}
        sa.Column('primary_style', sa.String(100), nullable=False),
        sa.Column('secondary_style', sa.String(100), nullable=True),
        sa.Column('style_message', sa.Text, nullable=False),
        sa.Column('scores', postgresql.JSONB, nullable=False),  # {Bohemian: 3, Classic: 1, ...}
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    op.create_index('ix_quiz_responses_user_id', 'quiz_responses', ['user_id'])
    op.create_index('ix_quiz_responses_completed_at', 'quiz_responses', ['completed_at'])


def downgrade() -> None:
    # Drop new tables
    op.drop_table('quiz_responses')
    op.drop_table('quiz_items')
    op.drop_table('style_categories')
    
    # Note: We're not recreating the old tables in downgrade
    # If you need to rollback, you'll need to restore from backup