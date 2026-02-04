"""
Manual migration applier - Run this ONLY if alembic stamp was used without upgrade
This applies the SQL from 2026_02_04_0001_sync_user_columns.py manually
"""
from sqlalchemy import create_engine, text
from app.config import settings

def apply_migration_sql():
    engine = create_engine(settings.DATABASE_URL)
    
    print("\n" + "="*80)
    print("MANUAL MIGRATION APPLICATION")
    print("="*80)
    
    statements = [
        # Create enum type
        "CREATE TYPE IF NOT EXISTS plantier AS ENUM ('free', 'premium', 'enterprise')",
        
        # Subscription identifiers
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS tier VARCHAR(50) NOT NULL DEFAULT 'free'",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(255)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS stripe_subscription_id VARCHAR(255)",
        
        # Commercial MVP fields
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS plan_tier plantier NOT NULL DEFAULT 'free'",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS paddle_subscription_id VARCHAR(255)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS paddle_customer_id VARCHAR(255)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_senior BOOLEAN NOT NULL DEFAULT false",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_military BOOLEAN NOT NULL DEFAULT false",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_firstresponder BOOLEAN NOT NULL DEFAULT false",
        
        # Preferences
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS voice_preference VARCHAR(50) NOT NULL DEFAULT 'none'",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS primary_mode VARCHAR(50) NOT NULL DEFAULT 'personal_friend'",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS silo_id VARCHAR(50)",
        
        # Usage tracking
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS message_count VARCHAR(255) NOT NULL DEFAULT '0'",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_message_reset TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()",
        
        # Voice limits
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS voice_limit INTEGER",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS voice_used INTEGER NOT NULL DEFAULT 0",
        
        # Admin/referral metadata
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin VARCHAR(10) NOT NULL DEFAULT 'false'",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS referral_code VARCHAR(20)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS referred_by UUID",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS referral_credits VARCHAR(255) NOT NULL DEFAULT '0'",
        
        # Memory & NEBP
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS global_memory JSON NOT NULL DEFAULT '{}'::json",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS nebp_phase VARCHAR(20) NOT NULL DEFAULT 'discovery'",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS nebp_clarity_metrics JSON NOT NULL DEFAULT '{}'::json",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS subscribed_personalities JSON NOT NULL DEFAULT '[\"personal_friend\",\"discovery_mode\"]'::json",
        
        # Accountability & tone controls
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS accountability_style VARCHAR(50) NOT NULL DEFAULT 'adaptive'",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS sentiment_override_enabled BOOLEAN NOT NULL DEFAULT true",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS depth_sensitivity_enabled BOOLEAN NOT NULL DEFAULT true",
        
        # Timestamp auditing
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login TIMESTAMP WITH TIME ZONE",
    ]
    
    index_statements = [
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_paddle_subscription_id ON users (paddle_subscription_id)",
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_paddle_customer_id ON users (paddle_customer_id)",
    ]
    
    try:
        with engine.connect() as conn:
            print("\n🔧 Applying migration SQL statements...")
            
            for i, stmt in enumerate(statements, 1):
                print(f"\n[{i}/{len(statements)}] {stmt[:60]}...")
                conn.execute(text(stmt))
                conn.commit()
                print("   ✅ Success")
            
            print("\n🔧 Creating indexes...")
            for i, stmt in enumerate(index_statements, 1):
                print(f"\n[{i}/{len(index_statements)}] {stmt[:60]}...")
                conn.execute(text(stmt))
                conn.commit()
                print("   ✅ Success")
            
            print("\n" + "="*80)
            print("✅ MIGRATION APPLIED SUCCESSFULLY")
            print("="*80)
            
            # Verify plan_tier now exists
            result = conn.execute(text("SELECT plan_tier FROM users LIMIT 1"))
            print(f"\n✅ Verified: plan_tier column exists with value: {result.scalar()}")
            
            return True
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import sys
    
    print("\n⚠️  WARNING: This script manually applies migration SQL.")
    print("⚠️  Only run this if you used 'alembic stamp head' without 'alembic upgrade head'")
    print("⚠️  The SQL uses IF NOT EXISTS so it's safe to run multiple times.")
    
    response = input("\nContinue? (yes/no): ")
    if response.lower() == 'yes':
        success = apply_migration_sql()
        sys.exit(0 if success else 1)
    else:
        print("Aborted.")
        sys.exit(0)
