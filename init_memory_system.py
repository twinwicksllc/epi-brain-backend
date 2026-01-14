"""
Initialize database and add memory fields

This script:
1. Creates all database tables if they don't exist
2. Adds memory fields to users and conversations tables
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import Base, engine
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.learning_pattern import LearningPattern
import sqlite3

def init_database():
    """Initialize all database tables"""
    print("🔄 Initializing database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Failed to create tables: {str(e)}")
        return False
    return True

def add_memory_fields():
    """Add memory fields to existing tables"""
    print("\n🔄 Adding memory fields...")
    
    try:
        db_path = os.path.join(os.path.dirname(__file__), 'epi_brain.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(users)")
        user_columns = [col[1] for col in cursor.fetchall()]
        
        cursor.execute("PRAGMA table_info(conversations)")
        conv_columns = [col[1] for col in cursor.fetchall()]
        
        # Add global_memory to users table if it doesn't exist
        if 'global_memory' not in user_columns:
            print("  Adding global_memory to users table...")
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN global_memory TEXT DEFAULT '{}';
            """)
            print("  ✓ global_memory added to users")
        else:
            print("  ⚠ global_memory already exists in users table")
        
        # Add session_memory to conversations table if it doesn't exist
        if 'session_memory' not in conv_columns:
            print("  Adding session_memory to conversations table...")
            cursor.execute("""
                ALTER TABLE conversations 
                ADD COLUMN session_memory TEXT DEFAULT '{}';
            """)
            print("  ✓ session_memory added to conversations")
        else:
            print("  ⚠ session_memory already exists in conversations table")
        
        conn.commit()
        conn.close()
        
        print("✅ Memory fields added successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to add memory fields: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("EPI Brain Memory System Initialization")
    print("=" * 60)
    
    # Step 1: Initialize database
    if not init_database():
        print("\n❌ Database initialization failed")
        sys.exit(1)
    
    # Step 2: Add memory fields
    if not add_memory_fields():
        print("\n❌ Memory fields addition failed")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ Memory system initialized successfully!")
    print("=" * 60)
    print("\n📊 Summary:")
    print("   - Database tables: Created")
    print("   - users.global_memory: Ready")
    print("   - conversations.session_memory: Ready")
    print("\n🚀 Memory system is ready to use!")

if __name__ == "__main__":
    main()