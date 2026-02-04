"""
Database Schema Checker
Run this script on production to verify which columns exist in the users table
"""
import sys
from sqlalchemy import create_engine, inspect, text
from app.config import settings

def check_database_schema():
    """Check the actual database schema for the users table"""
    try:
        engine = create_engine(settings.DATABASE_URL)
        inspector = inspect(engine)
        
        print("\n" + "="*80)
        print("DATABASE SCHEMA CHECK")
        print("="*80)
        
        # Check if users table exists
        tables = inspector.get_table_names()
        print(f"\n📊 Tables in database: {len(tables)}")
        print(f"   {', '.join(tables)}\n")
        
        if 'users' not in tables:
            print("❌ ERROR: 'users' table does not exist!")
            return False
        
        # Get all columns in users table
        columns = inspector.get_columns('users')
        column_names = [col['name'] for col in columns]
        
        print(f"✅ Users table exists with {len(columns)} columns:\n")
        
        # Expected columns from our User model
        expected_columns = [
            'id', 'email', 'password_hash',
            'tier', 'stripe_customer_id', 'stripe_subscription_id',
            'plan_tier', 'paddle_subscription_id', 'paddle_customer_id',
            'is_senior', 'is_military', 'is_firstresponder',
            'voice_preference', 'primary_mode', 'silo_id',
            'message_count', 'last_message_reset',
            'voice_limit', 'voice_used',
            'is_admin', 'referral_code', 'referred_by', 'referral_credits',
            'global_memory', 'nebp_phase', 'nebp_clarity_metrics', 'subscribed_personalities',
            'accountability_style', 'sentiment_override_enabled', 'depth_sensitivity_enabled',
            'created_at', 'updated_at', 'last_login'
        ]
        
        # Check which columns exist
        missing_columns = []
        for expected in expected_columns:
            if expected in column_names:
                print(f"   ✅ {expected}")
            else:
                print(f"   ❌ {expected} - MISSING!")
                missing_columns.append(expected)
        
        # Show unexpected columns
        unexpected = [col for col in column_names if col not in expected_columns]
        if unexpected:
            print(f"\n⚠️  Unexpected columns found:")
            for col in unexpected:
                print(f"   - {col}")
        
        # Check alembic version
        print("\n" + "="*80)
        print("ALEMBIC MIGRATION STATUS")
        print("="*80)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            current_version = result.scalar()
            print(f"\n📌 Current database migration version: {current_version}")
        
        expected_version = "2026_02_04_0001"
        if current_version == expected_version:
            print(f"   ✅ Database is at the latest migration ({expected_version})")
        else:
            print(f"   ⚠️  Database is at {current_version}, expected {expected_version}")
            print(f"   🔧 Run: alembic upgrade head")
        
        # Summary
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        
        if missing_columns:
            print(f"\n❌ {len(missing_columns)} columns are missing:")
            for col in missing_columns:
                print(f"   - {col}")
            print(f"\n🔧 Solution: Run 'alembic upgrade head' on production")
            return False
        else:
            print("\n✅ All expected columns exist!")
            if current_version != expected_version:
                print("⚠️  But migration version is outdated - run 'alembic upgrade head'")
                return False
            return True
            
    except Exception as e:
        print(f"\n❌ Error checking database schema: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = check_database_schema()
    sys.exit(0 if success else 1)
