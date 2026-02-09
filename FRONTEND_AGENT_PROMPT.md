# Frontend Issue: Guest Chat Sending Wrong Mode Value

## Problem Statement

The guest chat endpoint is failing with a 401 Unauthorized error on the production backend. The root cause has been identified: **the frontend is sending `mode: 'default'` when it should send `mode: 'discovery_mode'` (or omit the field entirely for guests)**.

## Root Cause Analysis

### Backend Logs Evidence
```
[DEBUG] POST /message - auth_header present: False, current_user: None, 
mode: 'default', discovery_mode_requested: False
[DEBUG] Rejecting unauthenticated request for non-discovery mode: default
```

This proves:
- ✅ No Authorization header is present (correct for guests)
- ✅ User is authenticated as None (correct for guests)
- ❌ Mode is 'default' (WRONG - should be 'discovery_mode')
- ❌ Backend rejects this as unauthorized (correct behavior)

### Why It Fails

1. Frontend calls the guest chat endpoint with `mode: 'default'`
2. Backend doesn't recognize 'default' as a valid personality mode
3. Backend requires authentication for unrecognized modes
4. Guest has no auth token → 401 Unauthorized

## Required Fix

### Task: Update Guest Chat Request

**Locate:** The frontend's "Public API client" or guest chat request handler (look for references to `/api/v1/chat/message`)

**Current behavior:**
```javascript
// ❌ WRONG - Sending unknown mode 'default' for guests
const response = await fetch('https://api.epibraingenius.com/api/v1/chat/message', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        message: userMessage,
        mode: 'default'  // ← This causes 401!
    })
});
```

**Expected behavior (pick ONE option):**

**Option A: Omit mode field (let backend default)**
```javascript
// ✅ CORRECT - Backend defaults to discovery_mode
const response = await fetch('https://api.epibraingenius.com/api/v1/chat/message', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        message: userMessage
        // mode field omitted → defaults to discovery_mode
    })
});
```

**Option B: Explicitly send discovery_mode**
```javascript
// ✅ CORRECT - Explicitly set to discovery_mode
const response = await fetch('https://api.epibraingenius.com/api/v1/chat/message', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        message: userMessage,
        mode: 'discovery_mode'  // ← explicitly set for guests
    })
});
```

**Option C: Send null or empty string**
```javascript
// ✅ CORRECT - Empty/null also defaults to discovery_mode
const response = await fetch('https://api.epibraingenius.com/api/v1/chat/message', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        message: userMessage,
        mode: ''  // or null → defaults to discovery_mode
    })
});
```

## Validation Rules

For **guest users** (unauthenticated):
- ✅ DO NOT send `Authorization` header
- ✅ Either omit `mode` field OR set to `'discovery_mode'` OR set to empty/null
- ✅ MUST include `message` field (required)
- ✅ Can optionally include `is_homepage_session: true` to track entry point

For **authenticated users**:
- ✅ MUST send `Authorization: Bearer <token>` header
- ✅ Can send `mode` as any value they're subscribed to (e.g., 'therapist', 'coach', 'personal_friend')
- ✅ MUST include `message` field (required)

## Testing After Fix

### Browser Console Test
```javascript
// Test 1: Verify correct payload structure
const payload = {
    message: "Hello, tell me about your features",
    // mode omitted or set to "discovery_mode"
};
console.log('Payload:', JSON.stringify(payload, null, 2));
console.log('Has Authorization header?', /* should be false */);

// Test 2: Make actual request
const response = await fetch('https://api.epibraingenius.com/api/v1/chat/message', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
});

console.log('Status:', response.status); // Should be 200, not 401
console.log('Response:', await response.json());
```

### cURL Verification (from terminal)
```bash
curl -X POST https://api.epibraingenius.com/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello there",
    "mode": "discovery_mode"
  }'

# Expected: 200 OK with chat response
# NOT: 401 Unauthorized
```

## Files to Check

Search the frontend codebase for:
1. `"default"` - Find where mode is set to this value
2. `/api/v1/chat/message` - Find all calls to this endpoint
3. `Public API client` - Look for any comments/class names mentioning this
4. `mode:` - Find all places where mode is assigned
5. `discovery_mode` - Check if it's already used elsewhere successfully

## Expected Result After Fix

**Backend logs will show:**
```
[DEBUG] POST /message - auth_header present: False, current_user: None, 
mode: 'discovery_mode', discovery_mode_requested: True
```

✅ No rejection
✅ Guest can chat
✅ AI response is returned

## Rollback Info

### For Backend Team (if needed)
The backend has been updated with a temporary fallback:
- When an unauthenticated user sends an unknown mode like 'default', it automatically converts it to 'discovery_mode'
- This means the frontend fix is NOT blocking, but still recommended for long-term stability
- The fallback will log: `Guest sent unknown mode 'default', defaulting to discovery_mode`

## Additional Context

**Why this matters:**
- EPI Brain has multiple personality modes (therapist, coach, mentor, etc.)
- Each requires the user to be subscribed (authenticated)
- Discovery mode is the free tier for unregistered users
- Frontend sends 'default' which isn't a valid personality → API rejects it

**Related files:**
- Backend validation: [app/api/chat.py line 520-535](https://github.com/twinwicksllc/epi-brain-backend/blob/main/app/api/chat.py#L520-L535)
- Request schema: [app/schemas/message.py line 33-52](https://github.com/twinwicksllc/epi-brain-backend/blob/main/app/schemas/message.py#L33-L52)
- Valid personalities: therapist, coach, mentor, personal_friend, motivator, psychologist, life_coach, wellness_advisor, psychology_expert

## Checklist

- [ ] Find where `mode: 'default'` is being set
- [ ] Change to `mode: 'discovery_mode'` OR remove mode field
- [ ] Verify no Authorization header is sent for guest requests
- [ ] Test in browser DevTools (should see 200 status, not 401)
- [ ] Test with cURL (provided above)
- [ ] Deploy to production
- [ ] Verify logs show correct mode value in backend
- [ ] Confirm guest chat works end-to-end

## Questions to Answer

1. Where is `mode: 'default'` being set?
2. Is this a configuration value or hardcoded in code?
3. Why was 'default' chosen instead of 'discovery_mode'?
4. Are there other places where the mode value needs to be updated?
5. Is there a mapping between frontend mode names and backend mode names?

---

**Backend is ready and waiting for frontend fix.** Deploy this change and guest chat should work immediately.
