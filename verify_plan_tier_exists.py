"""
Quick column existence checker - run this to verify plan_tier exists
"""
from sqlalchemy import create_engine, text
from app.config import settings

engine = create_engine(settings.DATABASE_URL)

with engine.connect() as conn:
    # Try to query the plan_tier column
    try:
        result = conn.execute(text("SELECT plan_tier FROM users LIMIT 1"))
        print("✅ SUCCESS: plan_tier column exists!")
        print(f"   Sample value: {result.scalar()}")
    except Exception as e:
        print("❌ ERROR: plan_tier column does NOT exist!")
        print(f"   Error: {e}")
        print("\n🔧 You need to manually apply the migration SQL.")
        print("   Run the SQL from alembic/versions/2026_02_04_0001_sync_user_columns.py")
