"""Migration: Add Semantic Memory System Tables"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine


def upgrade():
    """Create the semantic memory system tables"""
    
    print("Adding semantic memory system tables...")
    
    with engine.connect() as conn:
        try:
            # Add accountability preferences to users table
            print("  - Adding accountability preferences to users table...")
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS accountability_style VARCHAR(50) DEFAULT 'adaptive',
                ADD COLUMN IF NOT EXISTS sentiment_override_enabled BOOLEAN DEFAULT TRUE,
                ADD COLUMN IF NOT EXISTS depth_sensitivity_enabled BOOLEAN DEFAULT TRUE
            """))
            conn.commit()
            
            # Create semantic_memories table
            print("  - Creating semantic_memories table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS semantic_memories (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    mode VARCHAR(50) NOT NULL,
                    content TEXT NOT NULL,
                    importance_score FLOAT DEFAULT 0.5,
                    category VARCHAR(50),
                    source_conversation_id UUID,
                    source_message_id UUID,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    access_count FLOAT DEFAULT 0.0,
                    tags TEXT,
                    is_sensitive VARCHAR(10) DEFAULT 'false'
                )
            """))
            conn.commit()
            
            # Create indexes for semantic_memories
            print("  - Creating indexes for semantic_memories...")
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_semantic_memories_user_id ON semantic_memories(user_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_semantic_memories_mode ON semantic_memories(mode)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_semantic_memories_importance ON semantic_memories(importance_score)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_semantic_memories_created_at ON semantic_memories(created_at)"))
            conn.commit()
            
            # Create goals table
            print("  - Creating goals table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS goals (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    category VARCHAR(50) NOT NULL,
                    priority VARCHAR(50) NOT NULL DEFAULT 'medium',
                    status VARCHAR(50) NOT NULL DEFAULT 'not_started',
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP
                )
            """))
            conn.commit()
            
            # Create indexes for goals
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_goals_user_id ON goals(user_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_goals_status ON goals(status)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_goals_category ON goals(category)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_goals_created_at ON goals(created_at)"))
            conn.commit()
            
            # Create check_ins table
            print("  - Creating check_ins table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS check_ins (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    goal_id UUID NOT NULL REFERENCES goals(id) ON DELETE CASCADE,
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    notes TEXT,
                    mood VARCHAR(20),
                    energy_level INTEGER,
                    successful BOOLEAN DEFAULT FALSE,
                    progress_update TEXT,
                    obstacles_faced TEXT,
                    next_steps TEXT,
                    metrics TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
            
            # Create indexes for check_ins
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_check_ins_goal_id ON check_ins(goal_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_check_ins_user_id ON check_ins(user_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_check_ins_created_at ON check_ins(created_at)"))
            conn.commit()
            
            # Create milestones table
            print("  - Creating milestones table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS milestones (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    goal_id UUID NOT NULL REFERENCES goals(id) ON DELETE CASCADE,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    target_value FLOAT,
                    current_value FLOAT DEFAULT 0.0,
                    is_completed BOOLEAN DEFAULT FALSE,
                    completed_at TIMESTAMP,
                    target_date TIMESTAMP,
                    order_num INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
            
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_milestones_goal_id ON milestones(goal_id)"))
            conn.commit()
            
            # Create habits table
            print("  - Creating habits table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS habits (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    frequency VARCHAR(50) NOT NULL DEFAULT 'daily',
                    custom_days TEXT,
                    target_time VARCHAR(50),
                    trigger TEXT,
                    routine TEXT,
                    reward TEXT,
                    status VARCHAR(50) NOT NULL DEFAULT 'active',
                    current_streak_days INTEGER DEFAULT 0,
                    longest_streak_days INTEGER DEFAULT 0,
                    total_completions INTEGER DEFAULT 0,
                    created_by_mode VARCHAR(50) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    started_at TIMESTAMP
                )
            """))
            conn.commit()
            
            # Create indexes for habits
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_habits_user_id ON habits(user_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_habits_status ON habits(status)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_habits_created_at ON habits(created_at)"))
            conn.commit()
            
            # Create habit_completions table
            print("  - Creating habit_completions table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS habit_completions (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    habit_id UUID NOT NULL REFERENCES habits(id) ON DELETE CASCADE,
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT,
                    mood VARCHAR(20),
                    difficulty INTEGER
                )
            """))
            conn.commit()
            
            # Create indexes for habit_completions
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_habit_completions_habit_id ON habit_completions(habit_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_habit_completions_user_id ON habit_completions(user_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_habit_completions_completed_at ON habit_completions(completed_at)"))
            conn.commit()
            
            print("✅ Migration completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    success = upgrade()
    sys.exit(0 if success else 1)
