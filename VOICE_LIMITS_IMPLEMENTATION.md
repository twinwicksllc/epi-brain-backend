# Voice Interaction Limits & NEBP Metrics - Implementation Summary

## 📋 Changes Made

### 1. User Model Updates
**File:** `app/models/user.py`

Added two new columns to the `User` model to track voice interactions:
- `voice_limit: Integer` - Daily voice message limit (null = unlimited for admin/pro users)
- `voice_used: Integer` - Voice messages used today (default: 0)

### 2. User Response Schema
**File:** `app/schemas/user.py`

Updated `UserResponse` to include voice tracking fields:
- `voice_limit: Optional[int]` - Returns null for unlimited users (admins)
- `voice_used: int` - Returns the number of voice messages used today

### 3. /me Endpoint Enhancement
**File:** `app/api/users.py`

Updated `GET /api/v1/users/me` endpoint to:
- Calculate `voice_limit` based on user tier and admin status
  - Admins: `None` (unlimited)
  - Free tier: 10 messages/day
  - Pro tier: 50 messages/day
- Calculate `voice_used` by querying today's voice usage from the database
- Frontend receives these values and displays loading → actual limits

### 4. NEBP State Machine Fix
**File:** `app/services/nebp_state_machine.py`

Enhanced `calculate_clarity_metrics()` to handle legacy conversations:
- **Problem:** Legacy conversations (like "Tommy") didn't have `discovery_metadata`, so metrics weren't calculated
- **Solution:** 
  - For conversations with explicit `silo_id` (sales/spiritual/education), check message against silo keywords
  - For legacy conversations without `silo_id`, automatically detect any silo focus across all keyword sets
  - Metrics now calculate correctly even when `discovery_metadata` is None
  - `topic_clarity_score` and `silo_focus_identified` now work for both discovery mode and legacy conversations

## 🗄️ Database Migration

**File:** `alembic/versions/2026_02_03_0002_add_voice_limits.py`

Created migration to add:
- `voice_limit` column (Integer, nullable)
- `voice_used` column (Integer, default=0)

**To apply migration:**
```bash
alembic upgrade head
```

## 🔄 How It Works

### Frontend Loading Fix
1. Frontend calls `GET /api/v1/users/me`
2. Backend calculates voice limits dynamically:
   - Checks user tier and admin status
   - Queries today's voice usage from `voice_usage` table
   - Returns `voice_limit` and `voice_used` in response
3. Frontend receives values and displays actual metrics instead of "Loading..."

### Admin Users
- **voice_limit:** null (interpreted as unlimited by frontend)
- **voice_used:** Still tracked but displayed as "Unlimited"

### Free/Pro Users
- **voice_limit:** Set to 10 (free) or 50 (pro) based on tier
- **voice_used:** Current day's usage count

### NEBP Metrics for Legacy Conversations
- **Tommy session:** Now correctly calculates clarity metrics from message content
- **Phase progression:** Works even without explicit discovery_metadata
- **Backward compatible:** Doesn't break existing conversations

## ✅ Testing Recommendations

1. **Voice Limits:**
   - Test admin account → expects `voice_limit: null`
   - Test free account → expects `voice_limit: 10`
   - Test pro account → expects `voice_limit: 50`
   - Verify `voice_used` increases with each TTS call

2. **Tommy Session (Legacy):**
   - Verify NEBP metrics are calculated
   - Check `nebp_clarity_metrics` includes `topic_clarity_score`
   - Verify phase progression if action keywords are present

3. **No Breaking Changes:**
   - Existing voice tracking still works
   - All tier-based limits still enforced
   - Discovery mode metrics unchanged
