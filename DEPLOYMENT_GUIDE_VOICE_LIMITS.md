# Deployment Guide - Voice Limits & NEBP Metrics Fix

## Quick Overview
This update fixes:
1. Frontend "Loading..." issue for voice interaction limits
2. NEBP metrics calculation for legacy conversations (Tommy session)

## Pre-Deployment Checklist

- [x] Code changes implemented and tested
- [x] No syntax errors
- [x] All files compile successfully
- [x] Test suite passing
- [ ] Database backup created
- [ ] Ready to deploy to Render

## Deployment Steps

### Step 1: Backup Database (Recommended)
```bash
# On Render, backup your database before applying migrations
# https://render.com/docs/databases#backups
```

### Step 2: Apply Database Migration
```bash
cd /workspaces/epi-brain-backend
alembic upgrade head
```

This will add two columns to the `users` table:
- `voice_limit` (Integer, nullable) - Daily voice limit
- `voice_used` (Integer, default 0) - Today's usage count

### Step 3: Restart Backend Service
- Trigger a redeploy on Render
- Or restart the backend service

### Step 4: Verify Deployment

#### Test /me Endpoint:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.epibraingenius.com/api/v1/users/me

# Should see:
# "voice_limit": 10 (for free) or 50 (for pro) or null (for admin)
# "voice_used": 0 (or current day's usage)
```

#### Test Tommy Session:
```bash
# Make a message in Tommy conversation
# Check response metadata for nebp_clarity_metrics
# Should include: topic_clarity_score, silo_focus_identified, etc.
```

#### Test Frontend:
- Open dashboard
- Look at voice interaction limits
- Should show actual numbers (e.g., "3/10") instead of "Loading..."

## Rollback Plan

If issues occur:

### Option 1: Downgrade Migration
```bash
alembic downgrade -1
```

### Option 2: Manual Column Removal
```sql
ALTER TABLE users DROP COLUMN IF EXISTS voice_used;
ALTER TABLE users DROP COLUMN IF EXISTS voice_limit;
```

## Files Changed Summary

| File | Status | Notes |
|------|--------|-------|
| app/models/user.py | ✅ Modified | Added voice_limit, voice_used |
| app/schemas/user.py | ✅ Modified | Added voice fields to response |
| app/api/users.py | ✅ Modified | Updated /me endpoint logic |
| app/services/nebp_state_machine.py | ✅ Modified | Fixed legacy conversation handling |
| alembic/versions/2026_02_03_0002_add_voice_limits.py | ✅ New | Migration file |

## Expected Behavior After Deployment

### /me Endpoint Response
**Free User:**
```json
{
  "voice_limit": 10,
  "voice_used": 3,
  ...
}
```

**Pro User:**
```json
{
  "voice_limit": 50,
  "voice_used": 7,
  ...
}
```

**Admin User:**
```json
{
  "voice_limit": null,
  "voice_used": 15,
  ...
}
```

### Tommy Session
- NEBP metrics now calculate from message content
- `nebp_clarity_metrics` populated with topic_clarity_score
- Phase progression works for legacy conversations

## Testing Checklist

- [ ] /me endpoint returns voice_limit and voice_used
- [ ] Admin users get voice_limit: null
- [ ] Free users get voice_limit: 10
- [ ] Pro users get voice_limit: 50
- [ ] voice_used increments with TTS calls
- [ ] Tommy session shows NEBP metrics
- [ ] Frontend dashboard shows actual voice limits
- [ ] No errors in backend logs
- [ ] No breaking changes to existing features

## Monitoring After Deployment

### Key Logs to Check:
```
[INFO] Updated user profile with voice limits
[INFO] NEBP metrics calculated for legacy conversation
[WARNING] Voice limit exceeded for user X
```

### Metrics to Monitor:
- Error rate for /me endpoint (should be 0%)
- Response time for /me endpoint (should be <100ms)
- Voice usage accuracy (tracked = actual)
- NEBP phase progression in conversations

## Support

If issues occur:
1. Check backend logs for errors
2. Verify database migration applied: `alembic current`
3. Verify columns exist: `SELECT voice_limit, voice_used FROM users LIMIT 1`
4. Review VOICE_LIMITS_COMPLETE.md for detailed implementation

## Post-Deployment Verification

Run this in backend logs to verify:
```python
from app.models.user import User
from app.schemas.user import UserResponse

# Verify model has columns
assert hasattr(User, 'voice_limit')
assert hasattr(User, 'voice_used')
print("✅ User model has voice tracking fields")

# Verify schema has fields
assert 'voice_limit' in UserResponse.__fields__
assert 'voice_used' in UserResponse.__fields__
print("✅ UserResponse schema has voice fields")
```

## Timeline

- **Pre-deployment:** Database backup
- **Deployment:** Apply migration + restart service (5 min)
- **Verification:** Test endpoints + check logs (10 min)
- **Monitoring:** Watch for issues (1 hour)

## Done! 🎉

Voice interaction limits frontend issue is now fixed, and NEBP metrics are properly calculated for all conversations (both discovery mode and legacy).
