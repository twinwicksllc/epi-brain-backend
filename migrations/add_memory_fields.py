"""
Add memory fields to users and conversations tables

This migration adds:
- global_memory JSON field to users table (for persistent cross-session memory)
- session_memory JSON field to conversations table (for temporary session memory)

Run this script from the backend directory:
    python3 migrations/add_memory_fields.py
"""

import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3

def upgrade():
    """Add memory fields"""
    print("🔄 Starting memory fields migration...")
    
    try:
        # Connect to SQLite database
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'epi_brain.db')
        print(f"📦 Connecting to database: {db_path}")
        
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
        
        print("✅ Memory fields migration completed successfully!")
        print("📊 Summary:")
        print("   - users.global_memory: Ready")
        print("   - conversations.session_memory: Ready")
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def downgrade():
    """Remove memory fields"""
    print("🔄 Rolling back memory fields migration...")
    print("⚠ Note: SQLite doesn't support DROP COLUMN directly.")
    print("   Memory fields will remain but can be ignored.")
    print("   To fully remove, you would need to recreate the tables.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade()
    else:
        upgrade()