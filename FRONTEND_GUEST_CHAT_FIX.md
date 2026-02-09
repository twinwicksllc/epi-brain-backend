# Frontend Guest Chat Request Guide

## Issue: Getting 401 Unauthorized

The backend is correctly configured, but the frontend request is hitting the 401 error. This means the backend is receiving:
- No Authorization header ✅ (correct)
- A mode that is NOT "discovery_mode" ⚠️ (problem)
- No authenticated user ✅ (correct)

## Correct Guest Request Format

```javascript
// ✅ CORRECT - Minimal guest request
const response = await fetch('https://api.epibraingenius.com/api/v1/chat/message', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        // NO Authorization header
    },
    body: JSON.stringify({
        message: "Your message here",
        // DO NOT INCLUDE mode - let it default to "discovery_mode"
        // OR explicitly set mode: "discovery_mode"
    })
});
```

## What NOT to do

```javascript
// ❌ WRONG - Explicitly setting non-discovery mode
{
    message: "test",
    mode: "therapist"  // ← This requires authentication!
}

// ❌ WRONG - Sending Authorization header for guest
headers: {
    'Authorization': 'Bearer sometoken'  // ← Don't send this for guests
}

// ❌ WRONG - Missing required message field
{
    mode: "discovery_mode"
    // ← message is required
}
```

## Valid Guest Chat Payloads

### Option 1: Minimal (preferred for guests)
```json
{
    "message": "Hello, I want to learn more about this"
}
```
→ Will use `mode: "discovery_mode"` (default)
→ Will NOT require authentication

### Option 2: Explicit discovery mode
```json
{
    "message": "Hello, I want to learn more about this",
    "mode": "discovery_mode"
}
```
→ Explicitly shows discovery mode
→ Will NOT require authentication

### Option 3: Homepage quick start
```json
{
    "message": "Tell me about your features",
    "mode": "discovery_mode",
    "is_homepage_session": true,
    "entry_point": "homepage_quickstart"
}
```
→ Tracks where guest started
→ Will NOT require authentication

## Debugging Steps

### 1. Check Request Body in Browser
```javascript
// Add this before making the request to log what you're sending
const payload = {
    message: "test"
};
console.log('Sending:', JSON.stringify(payload, null, 2));
console.log('mode field included?', 'mode' in payload);
console.log('mode value:', payload.mode);
```

### 2. Check Request Headers
```javascript
// Verify no Authorization header is being sent
const response = await fetch('...', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        // Log all headers being sent
    },
    body: JSON.stringify(payload)
});
```

### 3. Check Response Details
```javascript
const response = await fetch('https://api.epibraingenius.com/api/v1/chat/message', {
    // ... your request
});

console.log('Status:', response.status);
console.log('Headers:', Array.from(response.headers.entries()));

if (!response.ok) {
    const error = await response.json();
    console.log('Error response:', error);
    console.log('Error detail:', error.detail);
}
```

## Backend Debug Logs

When you make a request, the backend now logs:
```
[DEBUG] POST /message - auth_header present: false, current_user: None, mode: 'discovery_mode', discovery_mode_requested: True
```

**If you see this:** ✅ Everything works correctly

**If you see different values:**
```
[DEBUG] POST /message - auth_header present: false, current_user: None, mode: 'personal_friend', discovery_mode_requested: False
```
→ You're sending `mode: "personal_friend"` which requires authentication
→ Change frontend to send `mode: "discovery_mode"` instead

## The Rules

For ANY guest request:
1. ✅ DO NOT send `Authorization` header
2. ✅ Either omit `mode` field (uses discovery_mode default) OR set `mode: "discovery_mode"`
3. ✅ Always include `message` (required field)
4. ✅ Never attempt to access authenticated endpoints like `/users/me`

For AUTHENTICATED user requests:
1. ✅ DO send `Authorization: Bearer <token>` header
2. ✅ Can send any `mode` value that user is subscribed to
3. ✅ Can access `/users/me` and other user endpoints

## Common Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| 401 Unauthorized | Mode is not discovery_mode | Send `mode: "discovery_mode"` or omit mode |
| 401 Unauthorized | Sending auth token for guest | Remove Authorization header |
| 422 Unprocessable Entity | Missing required `message` field | Add `message: "..."` to payload |
| 403 Forbidden | CORS preflight rejected | Check if origin is whitelisted |
| 503 Service Unavailable | Backend/Groq error | Check backend logs |

## Quick Test Command

```bash
curl -X POST https://api.epibraingenius.com/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, I want to learn more",
    "mode": "discovery_mode"
  }'

# Should return 200 with chat response, NOT 401
```

## Need More Help?

1. Make the request and watch the Network tab
2. Share the exact:
   - Request headers (especially Authorization)
   - Request body (what you're sending)
   - Response status (should be 200, not 401)
   - Response body (error message)
3. Check backend logs for the [DEBUG] message above
