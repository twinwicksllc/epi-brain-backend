#!/usr/bin/env python3
"""
Test script to verify voice limit changes:
- FREE: 10/day
- PRO: 50/day
- ADMIN: 999999 (unlimited)
"""
import sys
sys.path.insert(0, '/workspace/epi-brain-backend')

from app.config import settings

print("=" * 60)
print("VOICE LIMIT CONFIGURATION TEST")
print("=" * 60)
print()

print(f"FREE Tier Limit: {settings.VOICE_FREE_LIMIT} messages/day")
print(f"PRO Tier Limit: {settings.VOICE_PRO_LIMIT} messages/day")
print(f"ADMIN Tier Limit: {settings.VOICE_ADMIN_LIMIT} messages/day")
print()

# Verify the changes
assert settings.VOICE_FREE_LIMIT == 10, "FREE limit should be 10"
assert settings.VOICE_PRO_LIMIT == 50, "PRO limit should be 50"
assert settings.VOICE_ADMIN_LIMIT == 999999, "ADMIN limit should be 999999"

print("✅ All voice limit configurations are correct!")
print()

print("Expected Behavior:")
print("- FREE users: 10 voice messages per day")
print("- PRO users: 50 voice messages per day (increased from 10)")
print("- ADMIN users: Unlimited voice messages")
print()
print("=" * 60)