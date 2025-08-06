"""Add style assignment feedback table

Revision ID: 004
Revises: 003
Create Date: 2025-01-08 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    # Create style_assignment_feedback table
    op.create_table('style_assignment_feedback',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('quiz_response_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('accuracy_rating', sa.Integer(), nullable=False),
        sa.Column('preferred_style', sa.String(length=100), nullable=True),
        sa.Column('feedback_type', sa.String(length=50), nullable=False),
        sa.Column('feedback_text', sa.Text(), nullable=True),
        sa.Column('feature_feedback', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('accuracy_rating >= 1 AND accuracy_rating <= 5', name='check_accuracy_rating'),
        sa.CheckConstraint("feedback_type IN ('too_broad', 'too_narrow', 'completely_wrong', 'mostly_right', 'perfect')", name='check_feedback_type'),
        sa.ForeignKeyConstraint(['quiz_response_id'], ['quiz_responses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_style_assignment_feedback_quiz_response_id', 'style_assignment_feedback', ['quiz_response_id'])
    op.create_index('ix_style_assignment_feedback_user_id', 'style_assignment_feedback', ['user_id'])
    op.create_index('ix_style_assignment_feedback_feedback_type', 'style_assignment_feedback', ['feedback_type'])


def downgrade():
    # Drop indexes
    op.drop_index('ix_style_assignment_feedback_feedback_type', table_name='style_assignment_feedback')
    op.drop_index('ix_style_assignment_feedback_user_id', table_name='style_assignment_feedback')
    op.drop_index('ix_style_assignment_feedback_quiz_response_id', table_name='style_assignment_feedback')
    
    # Drop table
    op.drop_table('style_assignment_feedback')