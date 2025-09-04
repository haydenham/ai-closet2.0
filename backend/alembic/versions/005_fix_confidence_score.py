"""Fix confidence score precision

Revision ID: 005_fix_confidence_score
Revises: 004_add_style_feedback_table
Create Date: 2024-09-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    """Upgrade the confidence_score column to allow larger values"""
    # Modify quiz_responses.confidence_score
    op.alter_column('quiz_responses', 'confidence_score',
                   type_=sa.DECIMAL(5, 4),
                   existing_type=sa.DECIMAL(3, 2),
                   existing_nullable=True)
    
    # Modify feature_learning_data.confidence_score
    op.alter_column('feature_learning_data', 'confidence_score',
                   type_=sa.DECIMAL(5, 4),
                   existing_type=sa.DECIMAL(3, 2),
                   existing_nullable=True)


def downgrade():
    """Downgrade the confidence_score column back to original size"""
    # Revert quiz_responses.confidence_score
    op.alter_column('quiz_responses', 'confidence_score',
                   type_=sa.DECIMAL(3, 2),
                   existing_type=sa.DECIMAL(5, 4),
                   existing_nullable=True)
    
    # Revert feature_learning_data.confidence_score
    op.alter_column('feature_learning_data', 'confidence_score',
                   type_=sa.DECIMAL(3, 2),
                   existing_type=sa.DECIMAL(5, 4),
                   existing_nullable=True)
