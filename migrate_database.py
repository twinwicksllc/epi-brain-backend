"""
Database Migration Script
Adds missing columns to production database
"""

import os
from sqlalchemy import create_engine, text
from app.config import settings

def migrate_database():
    """Add missing columns to database"""
    
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        print("Starting database migration...")
        
        try:
            # Add global_memory to users table
            print("Adding global_memory column to users table...")
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS global_memory JSON DEFAULT '{}' NOT NULL
            """))
            conn.commit()
            print("✓ global_memory column added")
            
        except Exception as e:
            print(f"Note: global_memory column might already exist: {e}")
        
        try:
            # Add session_memory to conversations table
            print("Adding session_memory column to conversations table...")
            conn.execute(text("""
                ALTER TABLE conversations 
                ADD COLUMN IF NOT EXISTS session_memory JSON DEFAULT '{}' NOT NULL
            """))
            conn.commit()
            print("✓ session_memory column added")
            
        except Exception as e:
            print(f"Note: session_memory column might already exist: {e}")
        
        try:
            # Add is_admin to users table
            print("Adding is_admin column to users table...")
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS is_admin VARCHAR DEFAULT 'false' NOT NULL
            """))
            conn.commit()
            print("✓ is_admin column added")
            
        except Exception as e:
            print(f"Note: is_admin column might already exist: {e}")
        
        print("\nMigration complete!")
        print("You can now restart the backend service.")

if __name__ == "__main__":
    migrate_database()