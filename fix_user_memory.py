"""
Script to fix user memory data - removes "in CST" as name
"""
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

from app.models.user import User
from app.config import settings

def fix_user_memory():
    """Fix user memory by removing 'in CST' as name"""
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Get all users
        users = db.query(User).all()
        
        for user in users:
            if user.global_memory:
                memory = user.global_memory
                
                # Check if name is "in CST" or similar
                if isinstance(memory, dict):
                    if "user_profile" in memory:
                        profile = memory["user_profile"]
                        if "name" in profile:
                            name = profile["name"]
                            if name and name.lower() in ["in cst", "in", "cst"]:
                                print(f"Fixing user {user.id}: removing bad name '{name}'")
                                del profile["name"]
                                
                                # Mark as modified
                                from sqlalchemy.orm.attributes import flag_modified
                                flag_modified(user, "global_memory")
        
        db.commit()
        print("Memory fix complete!")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_user_memory()