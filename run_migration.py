"""
Manual migration script to add Phase 2 columns to users table
Run this on Render to add the missing columns
"""
import os
from sqlalchemy import create_engine, text

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set")
    exit(1)

# Create engine
engine = create_engine(DATABASE_URL)

# SQL to add missing columns
migration_sql = """
-- Add accountability columns to users table
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS accountability_style VARCHAR(50) DEFAULT 'adaptive',
ADD COLUMN IF NOT EXISTS sentiment_override_enabled VARCHAR(10) DEFAULT 'false',
ADD COLUMN IF NOT EXISTS depth_sensitivity_enabled VARCHAR(10) DEFAULT 'false';

-- Create Phase 2 tables
CREATE TABLE IF NOT EXISTS semantic_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    mode VARCHAR(50) NOT NULL,
    embedding TEXT NOT NULL,
    content TEXT NOT NULL,
    importance_score FLOAT DEFAULT 0.5,
    category VARCHAR(50),
    source_conversation_id UUID,
    source_message_id UUID,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    last_accessed TIMESTAMP DEFAULT NOW(),
    access_count FLOAT DEFAULT 0.0,
    tags TEXT,
    is_sensitive VARCHAR(10) DEFAULT 'false'
);

CREATE INDEX IF NOT EXISTS idx_semantic_memories_user ON semantic_memories(user_id);
CREATE INDEX IF NOT EXISTS idx_semantic_memories_mode ON semantic_memories(mode);
CREATE INDEX IF NOT EXISTS idx_semantic_memories_user_mode ON semantic_memories(user_id, mode);

CREATE TABLE IF NOT EXISTS goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL,
    priority VARCHAR(50) DEFAULT 'medium',
    status VARCHAR(50) DEFAULT 'not_started',
    progress_percentage FLOAT DEFAULT 0.0,
    specific_description TEXT,
    measurable_criteria TEXT,
    achievable_proof TEXT,
    relevance_reasoning TEXT,
    time_bound_deadline TIMESTAMP,
    current_streak_days INTEGER DEFAULT 0,
    longest_streak_days INTEGER DEFAULT 0,
    total_check_ins INTEGER DEFAULT 0,
    successful_check_ins INTEGER DEFAULT 0,
    accountability_style VARCHAR(50) DEFAULT 'adaptive',
    created_by_mode VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_goals_user ON goals(user_id);
CREATE INDEX IF NOT EXISTS idx_goals_status ON goals(status);

CREATE TABLE IF NOT EXISTS check_ins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    goal_id UUID NOT NULL REFERENCES goals(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    notes TEXT,
    mood VARCHAR(20),
    energy_level INTEGER,
    successful BOOLEAN DEFAULT false,
    progress_update TEXT,
    obstacles_faced TEXT,
    next_steps TEXT,
    metrics TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_check_ins_goal ON check_ins(goal_id);
CREATE INDEX IF NOT EXISTS idx_check_ins_user ON check_ins(user_id);

CREATE TABLE IF NOT EXISTS milestones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    goal_id UUID NOT NULL REFERENCES goals(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    target_value FLOAT,
    current_value FLOAT DEFAULT 0.0,
    is_completed BOOLEAN DEFAULT false,
    completed_at TIMESTAMP,
    target_date TIMESTAMP,
    "order" INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_milestones_goal ON milestones(goal_id);

CREATE TABLE IF NOT EXISTS habits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    frequency VARCHAR(50) DEFAULT 'daily',
    custom_days TEXT,
    target_time VARCHAR(50),
    trigger TEXT,
    routine TEXT,
    reward TEXT,
    status VARCHAR(50) DEFAULT 'active',
    current_streak_days INTEGER DEFAULT 0,
    longest_streak_days INTEGER DEFAULT 0,
    total_completions INTEGER DEFAULT 0,
    created_by_mode VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_habits_user ON habits(user_id);
CREATE INDEX IF NOT EXISTS idx_habits_status ON habits(status);

CREATE TABLE IF NOT EXISTS habit_completions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    habit_id UUID NOT NULL REFERENCES habits(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    completed_at TIMESTAMP DEFAULT NOW(),
    notes TEXT,
    mood VARCHAR(20),
    difficulty INTEGER
);

CREATE INDEX IF NOT EXISTS idx_habit_completions_habit ON habit_completions(habit_id);
CREATE INDEX IF NOT EXISTS idx_habit_completions_user ON habit_completions(user_id);
"""

try:
    with engine.connect() as conn:
        # Execute migration
        conn.execute(text(migration_sql))
        conn.commit()
        print("✓ Migration completed successfully!")
        print("✓ Added accountability columns to users table")
        print("✓ Created Phase 2 tables (goals, habits, semantic_memories, etc.)")
except Exception as e:
    print(f"✗ Migration failed: {e}")
    exit(1)
