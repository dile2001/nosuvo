"""Initial database schema

Revision ID: 0001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create initial database schema"""
    # Create exercises table
    op.create_table('exercises',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('language', sa.Text(), nullable=False),
        sa.Column('difficulty_level', sa.Integer(), nullable=True),
        sa.Column('word_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.Text(), nullable=False),
        sa.Column('email', sa.Text(), nullable=False),
        sa.Column('password_hash', sa.Text(), nullable=False),
        sa.Column('preferred_language', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('last_login', sa.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )
    
    # Create user_progress table
    op.create_table('user_progress',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('exercise_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Text(), nullable=False),
        sa.Column('comprehension_score', sa.Float(), nullable=True),
        sa.Column('questions_answered', sa.Integer(), nullable=True),
        sa.Column('questions_correct', sa.Integer(), nullable=True),
        sa.Column('reading_speed_wpm', sa.Float(), nullable=True),
        sa.Column('session_duration_seconds', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('completed_at', sa.TIMESTAMP(), nullable=True),
        sa.ForeignKeyConstraint(['exercise_id'], ['exercises.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'exercise_id')
    )
    
    # Create user_queue table
    op.create_table('user_queue',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('exercise_id', sa.Integer(), nullable=False),
        sa.Column('queue_position', sa.Integer(), nullable=False),
        sa.Column('added_at', sa.TIMESTAMP(), nullable=True),
        sa.ForeignKeyConstraint(['exercise_id'], ['exercises.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'exercise_id')
    )
    
    # Create indexes
    op.create_index('idx_exercises_language', 'exercises', ['language'])
    op.create_index('idx_exercises_difficulty', 'exercises', ['difficulty_level'])
    op.create_index('idx_user_progress_user_id', 'user_progress', ['user_id'])
    op.create_index('idx_user_progress_exercise_id', 'user_progress', ['exercise_id'])
    op.create_index('idx_user_progress_status', 'user_progress', ['status'])
    op.create_index('idx_user_queue_user_id', 'user_queue', ['user_id'])
    op.create_index('idx_user_queue_position', 'user_queue', ['queue_position'])


def downgrade():
    """Drop all tables"""
    op.drop_index('idx_user_queue_position', table_name='user_queue')
    op.drop_index('idx_user_queue_user_id', table_name='user_queue')
    op.drop_index('idx_user_progress_status', table_name='user_progress')
    op.drop_index('idx_user_progress_exercise_id', table_name='user_progress')
    op.drop_index('idx_user_progress_user_id', table_name='user_progress')
    op.drop_index('idx_exercises_difficulty', table_name='exercises')
    op.drop_index('idx_exercises_language', table_name='exercises')
    
    op.drop_table('user_queue')
    op.drop_table('user_progress')
    op.drop_table('users')
    op.drop_table('exercises')
