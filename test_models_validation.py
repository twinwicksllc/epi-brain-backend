"""
Validation test for AdminUsageResponse and UserUsageStats models
"""

from datetime import datetime
from app.api.admin import UserUsageStats, AdminUsageResponse
from app.models.user import PlanTier

def test_user_usage_stats_edge_cases():
    """Test UserUsageStats with various edge cases"""
    
    print("=" * 80)
    print("Testing UserUsageStats Model")
    print("=" * 80)
    
    # Test 1: Minimal valid data
    print("\n1. Minimal valid data...")
    try:
        stats = UserUsageStats(
            user_id="123e4567-e89b-12d3-a456-426614174000",
            email="test@example.com"
        )
        print(f"✅ Success: {stats}")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 2: All fields with None values
    print("\n2. All fields with None values...")
    try:
        stats = UserUsageStats(
            user_id=None,
            email=None,
            plan_tier=None,
            last_login=None,
            total_tokens_month=None,
            total_messages_month=None,
            total_cost_month=None,
            voice_used_month=None,
            voice_limit=None,
            is_admin=None,
            created_at=None
        )
        print(f"✅ Success: {stats}")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 3: All fields with valid data
    print("\n3. All fields with valid data...")
    try:
        stats = UserUsageStats(
            user_id="123e4567-e89b-12d3-a456-426614174000",
            email="user@example.com",
            plan_tier=PlanTier.PREMIUM,
            last_login=datetime.utcnow(),
            total_tokens_month=1000,
            total_messages_month=50,
            total_cost_month=25.50,
            voice_used_month=10,
            voice_limit=100,
            is_admin=True,
            created_at=datetime.utcnow()
        )
        print(f"✅ Success: {stats}")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 4: Mixed valid and None values
    print("\n4. Mixed valid and None values...")
    try:
        stats = UserUsageStats(
            user_id="123e4567-e89b-12d3-a456-426614174000",
            email="user@example.com",
            plan_tier=PlanTier.FREE,
            last_login=None,
            total_tokens_month=0,
            total_messages_month=0,
            total_cost_month=0.0,
            voice_used_month=0,
            voice_limit=None,
            is_admin=False,
            created_at=None
        )
        print(f"✅ Success: {stats}")
    except Exception as e:
        print(f"❌ Failed: {e}")


def test_admin_usage_response_edge_cases():
    """Test AdminUsageResponse with various edge cases"""
    
    print("\n" + "=" * 80)
    print("Testing AdminUsageResponse Model")
    print("=" * 80)
    
    # Test 1: Empty users list
    print("\n1. Empty users list...")
    try:
        response = AdminUsageResponse(
            success=True,
            period_start=datetime.utcnow(),
            period_end=datetime.utcnow(),
            total_users=0,
            users=[],
            summary={}
        )
        print(f"✅ Success: Response with {len(response.users)} users")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 2: Users with mixed data
    print("\n2. Users with mixed data...")
    try:
        users = [
            UserUsageStats(
                user_id="123e4567-e89b-12d3-a456-426614174000",
                email="user1@example.com",
                plan_tier=PlanTier.FREE
            ),
            UserUsageStats(
                user_id=None,
                email=None,
                plan_tier=None
            ),
            UserUsageStats(
                user_id="223e4567-e89b-12d3-a456-426614174000",
                email="user2@example.com",
                plan_tier=PlanTier.PREMIUM,
                total_tokens_month=5000,
                total_cost_month=100.0,
                is_admin=True
            )
        ]
        response = AdminUsageResponse(
            success=True,
            period_start=datetime.utcnow(),
            period_end=datetime.utcnow(),
            total_users=3,
            users=users,
            summary={
                "total_tokens_all_users": 5000,
                "total_messages_all_users": 50,
                "total_cost_all_users": 100.0,
                "total_voice_all_users": 0,
                "avg_tokens_per_user": 1666.67,
                "avg_cost_per_user": 33.33,
                "users_by_plan": {
                    "free": 1,
                    "premium": 1,
                    "enterprise": 0
                }
            }
        )
        print(f"✅ Success: Response with {len(response.users)} users")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 3: Complex summary
    print("\n3. Complex summary with various types...")
    try:
        response = AdminUsageResponse(
            success=True,
            period_start=datetime(2025, 2, 1),
            period_end=datetime(2025, 3, 1),
            total_users=10,
            users=[],
            summary={
                "total_tokens_all_users": 50000,
                "total_messages_all_users": 500,
                "total_cost_all_users": 250.75,
                "avg_cost_per_user": 25.075,
                "arbitrary_field": "can_be_anything",
                "nested_data": {
                    "level1": {
                        "level2": "value"
                    }
                }
            }
        )
        print(f"✅ Success: Response with complex summary")
    except Exception as e:
        print(f"❌ Failed: {e}")


if __name__ == "__main__":
    test_user_usage_stats_edge_cases()
    test_admin_usage_response_edge_cases()
    print("\n" + "=" * 80)
    print("Validation Tests Complete")
    print("=" * 80)
