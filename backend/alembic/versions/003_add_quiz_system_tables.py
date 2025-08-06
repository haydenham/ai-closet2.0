"""Add quiz system tables

Revision ID: 003
Revises: 002
Create Date: 2025-01-08 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create quiz_clothing_items table
    op.create_table('quiz_clothing_items',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('image_url', sa.String(length=500), nullable=False),
        sa.Column('gender', sa.String(length=10), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('features', sa.JSON(), nullable=False),
        sa.Column('auto_extracted_features', sa.JSON(), nullable=True),
        sa.Column('feature_confidence_scores', sa.JSON(), nullable=True),
        sa.Column('selection_count', sa.Integer(), nullable=False),
        sa.Column('satisfaction_score', sa.DECIMAL(precision=3, scale=2), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("gender IN ('male', 'female')", name='check_gender'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_quiz_clothing_items_category'), 'quiz_clothing_items', ['category'], unique=False)
    op.create_index(op.f('ix_quiz_clothing_items_gender'), 'quiz_clothing_items', ['gender'], unique=False)

    # Create style_categories table
    op.create_table('style_categories',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('gender', sa.String(length=10), nullable=False),
        sa.Column('features', sa.JSON(), nullable=False),
        sa.Column('ai_theme_prompt', sa.Text(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("gender IN ('male', 'female')", name='check_category_gender'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_style_categories_gender'), 'style_categories', ['gender'], unique=False)

    # Create quiz_responses table
    op.create_table('quiz_responses',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('selected_item_ids', sa.JSON(), nullable=False),
        sa.Column('calculated_scores', sa.JSON(), nullable=False),
        sa.Column('assigned_category', sa.String(length=100), nullable=False),
        sa.Column('assigned_category_id', sa.UUID(), nullable=True),
        sa.Column('confidence_score', sa.DECIMAL(precision=3, scale=2), nullable=True),
        sa.Column('user_satisfaction_rating', sa.Integer(), nullable=True),
        sa.Column('user_feedback_text', sa.Text(), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('user_satisfaction_rating >= 1 AND user_satisfaction_rating <= 5', name='check_satisfaction_rating'),
        sa.ForeignKeyConstraint(['assigned_category_id'], ['style_categories.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_quiz_responses_user_id'), 'quiz_responses', ['user_id'], unique=False)

    # Create quiz_response_items table
    op.create_table('quiz_response_items',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('quiz_response_id', sa.UUID(), nullable=False),
        sa.Column('clothing_item_id', sa.UUID(), nullable=False),
        sa.Column('question_category', sa.String(length=50), nullable=False),
        sa.Column('weight', sa.DECIMAL(precision=3, scale=2), nullable=True),
        sa.ForeignKeyConstraint(['clothing_item_id'], ['quiz_clothing_items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['quiz_response_id'], ['quiz_responses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create feature_learning_data table
    op.create_table('feature_learning_data',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('feature_name', sa.String(length=100), nullable=False),
        sa.Column('item_id', sa.UUID(), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('confidence_score', sa.DECIMAL(precision=3, scale=2), nullable=True),
        sa.Column('validation_count', sa.Integer(), nullable=False),
        sa.Column('rejection_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("source IN ('manual', 'cv_auto', 'user_suggested', 'algorithm_discovered')", name='check_feature_source'),
        sa.ForeignKeyConstraint(['item_id'], ['quiz_clothing_items.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_feature_learning_data_feature_name'), 'feature_learning_data', ['feature_name'], unique=False)
    op.create_index(op.f('ix_feature_learning_data_source'), 'feature_learning_data', ['source'], unique=False)

    # Create feature_correlations table
    op.create_table('feature_correlations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('feature_a', sa.String(length=100), nullable=False),
        sa.Column('feature_b', sa.String(length=100), nullable=False),
        sa.Column('correlation_strength', sa.DECIMAL(precision=3, scale=2), nullable=True),
        sa.Column('co_occurrence_count', sa.Integer(), nullable=False),
        sa.Column('total_occurrences', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_feature_correlations_feature_a'), 'feature_correlations', ['feature_a'], unique=False)
    op.create_index(op.f('ix_feature_correlations_feature_b'), 'feature_correlations', ['feature_b'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f('ix_feature_correlations_feature_b'), table_name='feature_correlations')
    op.drop_index(op.f('ix_feature_correlations_feature_a'), table_name='feature_correlations')
    op.drop_table('feature_correlations')
    
    op.drop_index(op.f('ix_feature_learning_data_source'), table_name='feature_learning_data')
    op.drop_index(op.f('ix_feature_learning_data_feature_name'), table_name='feature_learning_data')
    op.drop_table('feature_learning_data')
    
    op.drop_table('quiz_response_items')
    
    op.drop_index(op.f('ix_quiz_responses_user_id'), table_name='quiz_responses')
    op.drop_table('quiz_responses')
    
    op.drop_index(op.f('ix_style_categories_gender'), table_name='style_categories')
    op.drop_table('style_categories')
    
    op.drop_index(op.f('ix_quiz_clothing_items_gender'), table_name='quiz_clothing_items')
    op.drop_index(op.f('ix_quiz_clothing_items_category'), table_name='quiz_clothing_items')
    op.drop_table('quiz_clothing_items')