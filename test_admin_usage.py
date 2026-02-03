"""
Test script for Admin Usage Reporting endpoint
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
ADMIN_API_KEY = "your-admin-key-here"  # Replace with actual admin key

def test_admin_usage_endpoint():
    """Test the GET /api/v1/admin/usage endpoint"""
    
    print("=" * 80)
    print("Testing Admin Usage Reporting Endpoint")
    print("=" * 80)
    
    # Test 1: Get usage sorted by tokens (default)
    print("\n1. Testing usage report sorted by tokens...")
    response = requests.get(
        f"{BASE_URL}/api/v1/admin/usage",
        headers={"X-Admin-Key": ADMIN_API_KEY},
        params={"limit": 10, "sort_by": "tokens"}
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success!")
        print(f"Period: {data['period_start']} to {data['period_end']}")
        print(f"Total Users: {data['total_users']}")
        print(f"\nSummary Statistics:")
        print(json.dumps(data['summary'], indent=2))
        
        print(f"\nTop Users by Token Consumption:")
        for idx, user in enumerate(data['users'][:5], 1):
            print(f"\n{idx}. {user['email']}")
            print(f"   Plan: {user['plan_tier']}")
            print(f"   Tokens: {user['total_tokens_month']:,}")
            print(f"   Messages: {user['total_messages_month']}")
            print(f"   Cost: ${user['total_cost_month']:.4f}")
            print(f"   Voice Used: {user['voice_used_month']}")
            print(f"   Last Login: {user['last_login']}")
    else:
        print(f"❌ Failed: {response.text}")
    
    # Test 2: Get usage sorted by cost
    print("\n" + "=" * 80)
    print("2. Testing usage report sorted by cost...")
    response = requests.get(
        f"{BASE_URL}/api/v1/admin/usage",
        headers={"X-Admin-Key": ADMIN_API_KEY},
        params={"limit": 10, "sort_by": "cost"}
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success!")
        print(f"\nTop Users by Cost:")
        for idx, user in enumerate(data['users'][:5], 1):
            print(f"{idx}. {user['email']}: ${user['total_cost_month']:.4f}")
    else:
        print(f"❌ Failed: {response.text}")
    
    # Test 3: Get usage sorted by messages
    print("\n" + "=" * 80)
    print("3. Testing usage report sorted by messages...")
    response = requests.get(
        f"{BASE_URL}/api/v1/admin/usage",
        headers={"X-Admin-Key": ADMIN_API_KEY},
        params={"limit": 10, "sort_by": "messages"}
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success!")
        print(f"\nTop Users by Message Count:")
        for idx, user in enumerate(data['users'][:5], 1):
            print(f"{idx}. {user['email']}: {user['total_messages_month']} messages")
    else:
        print(f"❌ Failed: {response.text}")
    
    # Test 4: Get usage sorted by voice
    print("\n" + "=" * 80)
    print("4. Testing usage report sorted by voice...")
    response = requests.get(
        f"{BASE_URL}/api/v1/admin/usage",
        headers={"X-Admin-Key": ADMIN_API_KEY},
        params={"limit": 10, "sort_by": "voice"}
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success!")
        print(f"\nTop Users by Voice Usage:")
        for idx, user in enumerate(data['users'][:5], 1):
            voice_limit = user['voice_limit'] if user['voice_limit'] else "Unlimited"
            print(f"{idx}. {user['email']}: {user['voice_used_month']} / {voice_limit}")
    else:
        print(f"❌ Failed: {response.text}")
    
    # Test 5: Test without admin key (should fail)
    print("\n" + "=" * 80)
    print("5. Testing without admin key (should fail with 403)...")
    response = requests.get(
        f"{BASE_URL}/api/v1/admin/usage",
        params={"limit": 10}
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 403:
        print(f"✅ Correctly blocked unauthorized request")
    else:
        print(f"❌ Expected 403, got {response.status_code}")
    
    print("\n" + "=" * 80)
    print("Admin Usage Endpoint Testing Complete")
    print("=" * 80)


if __name__ == "__main__":
    test_admin_usage_endpoint()
