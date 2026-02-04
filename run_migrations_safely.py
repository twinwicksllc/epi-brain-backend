"""
Safe Migration Runner
Run this script on production to apply all pending migrations
"""
import sys
import subprocess
from sqlalchemy import create_engine, text
from app.config import settings

def get_current_version():
    """Get current migration version from database"""
    try:
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            return result.scalar()
    except Exception as e:
        print(f"⚠️  Could not get current version: {e}")
        return None

def run_migrations():
    """Run alembic migrations with safety checks"""
    print("\n" + "="*80)
    print("MIGRATION RUNNER")
    print("="*80)
    
    # Check current version
    current = get_current_version()
    if current:
        print(f"\n📌 Current migration version: {current}")
    else:
        print("\n⚠️  Could not determine current migration version")
        response = input("Continue anyway? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted.")
            return False
    
    # Show pending migrations
    print("\n🔍 Checking for pending migrations...")
    result = subprocess.run(
        ["alembic", "current"],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    
    # Run upgrade
    print("\n🚀 Running: alembic upgrade head")
    print("="*80)
    
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        capture_output=False,  # Show output in real-time
        text=True
    )
    
    if result.returncode == 0:
        print("\n" + "="*80)
        print("✅ MIGRATIONS COMPLETED SUCCESSFULLY")
        print("="*80)
        
        # Verify new version
        new_version = get_current_version()
        if new_version:
            print(f"\n📌 New migration version: {new_version}")
            if new_version == "2026_02_04_0001":
                print("✅ Database is now at the latest version!")
                return True
            else:
                print(f"⚠️  Expected 2026_02_04_0001 but got {new_version}")
                return False
        return True
    else:
        print("\n" + "="*80)
        print("❌ MIGRATION FAILED")
        print("="*80)
        print(f"\nExit code: {result.returncode}")
        return False

if __name__ == "__main__":
    success = run_migrations()
    sys.exit(0 if success else 1)
