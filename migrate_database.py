"""
Database Migration Script
Adds missing columns to production database
"""

import os
import sys
from sqlalchemy import create_engine, text, inspect

def migrate_database():
    """Add missing columns to database"""
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)
    
    print(f"Connecting to database...")
    engine = create_engine(database_url)
    
    # Check existing columns
    inspector = inspect(engine)
    
    with engine.connect() as conn:
        print("\n" + "="*50)
        print("DATABASE MIGRATION STARTING")
        print("="*50 + "\n")
        
        # Check users table
        print("Checking users table...")
        users_columns = [col['name'] for col in inspector.get_columns('users')]
        print(f"Existing columns: {', '.join(users_columns)}")
        
        # Add global_memory to users table
        if 'global_memory' not in users_columns:
            try:
                print("\n→ Adding global_memory column to users table...")
                conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN global_memory JSON DEFAULT '{}' NOT NULL
                """))
                conn.commit()
                print("✓ global_memory column added successfully")
            except Exception as e:
                print(f"✗ Error adding global_memory: {e}")
                conn.rollback()
        else:
            print("✓ global_memory column already exists")
        
        # Add is_admin to users table
        if 'is_admin' not in users_columns:
            try:
                print("\n→ Adding is_admin column to users table...")
                conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN is_admin VARCHAR DEFAULT 'false' NOT NULL
                """))
                conn.commit()
                print("✓ is_admin column added successfully")
            except Exception as e:
                print(f"✗ Error adding is_admin: {e}")
                conn.rollback()
        else:
            print("✓ is_admin column already exists")
        
        # Check conversations table
        print("\n" + "-"*50)
        print("Checking conversations table...")
        conversations_columns = [col['name'] for col in inspector.get_columns('conversations')]
        print(f"Existing columns: {', '.join(conversations_columns)}")
        
        # Add session_memory to conversations table
        if 'session_memory' not in conversations_columns:
            try:
                print("\n→ Adding session_memory column to conversations table...")
                conn.execute(text("""
                    ALTER TABLE conversations 
                    ADD COLUMN session_memory JSON DEFAULT '{}' NOT NULL
                """))
                conn.commit()
                print("✓ session_memory column added successfully")
            except Exception as e:
                print(f"✗ Error adding session_memory: {e}")
                conn.rollback()
        else:
            print("✓ session_memory column already exists")
        
        print("\n" + "="*50)
        print("MIGRATION COMPLETE!")
        print("="*50)
        print("\nYou can now uncomment the columns in the models and redeploy.")

if __name__ == "__main__":
    migrate_database()