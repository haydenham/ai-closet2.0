"""Initial database setup

Revision ID: 001
Revises: 
Create Date: 2025-01-08 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_setup'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial database tables"""
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('is_verified', sa.Boolean(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=False)
    
    # Create email verification tokens table
    op.create_table(
        'email_verification_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('token', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token')
    )
    op.create_index(op.f('ix_email_verification_tokens_token'), 'email_verification_tokens', ['token'], unique=False)
    
    # Create password reset tokens table
    op.create_table(
        'password_reset_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('token', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token')
    )
    op.create_index(op.f('ix_password_reset_tokens_token'), 'password_reset_tokens', ['token'], unique=False)
    
    # Create style profiles table
    op.create_table(
        'style_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('quiz_responses', sa.JSON(), nullable=False),
        sa.Column('assigned_model', sa.String(length=100), nullable=False),
        sa.Column('style_preferences', sa.JSON(), nullable=False),
        sa.Column('fashion_goals', sa.JSON(), nullable=True),
        sa.Column('preferred_colors', sa.JSON(), nullable=True),
        sa.Column('body_type', sa.String(length=50), nullable=True),
        sa.Column('lifestyle', sa.String(length=100), nullable=True),
        sa.Column('budget_range', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_style_profiles_user_id'), 'style_profiles', ['user_id'], unique=False)
    
    # Create quiz questions table
    op.create_table(
        'quiz_questions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('question_key', sa.String(length=100), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('question_type', sa.String(length=50), nullable=False),
        sa.Column('options', sa.JSON(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('question_key')
    )
    op.create_index(op.f('ix_quiz_questions_question_key'), 'quiz_questions', ['question_key'], unique=False)
    
    # Create clothing categories table
    op.create_table(
        'clothing_categories',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('parent_category_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['parent_category_id'], ['clothing_categories.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_clothing_categories_name'), 'clothing_categories', ['name'], unique=False)
    
    # Create clothing items table
    op.create_table(
        'clothing_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('image_url', sa.String(length=500), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('color', sa.String(length=50), nullable=True),
        sa.Column('brand', sa.String(length=100), nullable=True),
        sa.Column('size', sa.String(length=20), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('embedding', sa.JSON(), nullable=True),
        sa.Column('image_width', sa.Integer(), nullable=True),
        sa.Column('image_height', sa.Integer(), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('times_recommended', sa.Integer(), nullable=False),
        sa.Column('last_recommended', sa.DateTime(timezone=True), nullable=True),
        sa.Column('upload_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['category_id'], ['clothing_categories.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_clothing_items_user_id'), 'clothing_items', ['user_id'], unique=False)
    op.create_index(op.f('ix_clothing_items_category'), 'clothing_items', ['category'], unique=False)
    
    # Create outfit recommendations table
    op.create_table(
        'outfit_recommendations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('prompt', sa.Text(), nullable=False),
        sa.Column('ai_response', sa.Text(), nullable=False),
        sa.Column('outfit_components', sa.JSON(), nullable=True),
        sa.Column('ai_model_used', sa.String(length=100), nullable=False),
        sa.Column('occasion', sa.String(length=100), nullable=True),
        sa.Column('weather', sa.String(length=50), nullable=True),
        sa.Column('season', sa.String(length=20), nullable=True),
        sa.Column('feedback_score', sa.Integer(), nullable=True),
        sa.Column('feedback_comments', sa.Text(), nullable=True),
        sa.Column('is_favorite', sa.Boolean(), nullable=False),
        sa.Column('is_archived', sa.Boolean(), nullable=False),
        sa.Column('processing_time_ms', sa.Integer(), nullable=True),
        sa.Column('similarity_scores', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_outfit_recommendations_user_id'), 'outfit_recommendations', ['user_id'], unique=False)
    
    # Create outfit clothing items association table
    op.create_table(
        'outfit_clothing_items',
        sa.Column('outfit_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('clothing_item_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['clothing_item_id'], ['clothing_items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['outfit_id'], ['outfit_recommendations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('outfit_id', 'clothing_item_id')
    )
    
    # Create recommendation feedback table
    op.create_table(
        'recommendation_feedback',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('recommendation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('feedback_type', sa.String(length=50), nullable=False),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('style_accuracy', sa.Integer(), nullable=True),
        sa.Column('item_matching', sa.Integer(), nullable=True),
        sa.Column('occasion_appropriateness', sa.Integer(), nullable=True),
        sa.Column('feedback_tags', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['recommendation_id'], ['outfit_recommendations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_recommendation_feedback_recommendation_id'), 'recommendation_feedback', ['recommendation_id'], unique=False)
    op.create_index(op.f('ix_recommendation_feedback_user_id'), 'recommendation_feedback', ['user_id'], unique=False)


def downgrade() -> None:
    """Drop initial database tables"""
    
    # Drop tables in reverse order to handle foreign key constraints
    op.drop_table('recommendation_feedback')
    op.drop_table('outfit_clothing_items')
    op.drop_table('outfit_recommendations')
    op.drop_table('clothing_items')
    op.drop_table('clothing_categories')
    op.drop_table('quiz_questions')
    op.drop_table('style_profiles')
    op.drop_table('password_reset_tokens')
    op.drop_table('email_verification_tokens')
    op.drop_table('users')