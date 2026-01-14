"""Migration to add is_admin column to users table"""

from sqlalchemy import text
from app.database import engine

def migrate():
    """Add is_admin column to users table"""
    with engine.connect() as conn:
        try:
            # Check if column exists
            result = conn.execute(text("""
                SELECT COUNT(*) as count 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'is_admin'
            """))
            column_exists = result.fetchone()[0] > 0
            
            if not column_exists:
                # Add the column
                conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN is_admin VARCHAR(10) NOT NULL DEFAULT 'false'
                """))
                conn.commit()
                print("✅ Successfully added is_admin column to users table")
            else:
                print("ℹ️  is_admin column already exists in users table")
                
        except Exception as e:
            print(f"❌ Error adding is_admin column: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    migrate()