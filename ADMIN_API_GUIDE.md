# Admin API Guide

## Overview
The Admin API provides endpoints for managing users, upgrading account tiers, and viewing platform statistics. These endpoints are protected by an admin API key.

## Setup

### 1. Generate Admin API Key
Generate a secure admin API key:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Example output: `xK7jP9mN2qR5tY8wA3bC6dE1fG4hJ0iL`

### 2. Add to Environment Variables

**Local Development:**
```bash
# epi-brain-backend/.env
ADMIN_API_KEY=your-generated-key-here
```

**Render Production:**
- Go to Render Dashboard → epi-brain-backend → Environment
- Add: `ADMIN_API_KEY` = your-generated-key-here
- Save and redeploy

### 3. Restart Backend
The backend will need to restart to load the new environment variable.

## Admin API Endpoints

### Base URL
```
https://api.epibraingenius.com/api/v1/admin
```

### Authentication
All admin endpoints require the admin API key in the query string:
```
?admin_key=your-admin-key-here
```

## Endpoints

### 1. Upgrade User Tier
**Endpoint:** `POST /api/v1/admin/users/{user_id}/upgrade-tier`

**Description:** Upgrade a user's subscription tier

**Parameters:**
- `user_id` (path): User ID to upgrade
- `admin_key` (query): Admin API key
- `tier` (body): New tier (FREE, PRO, ENTERPRISE)

**Request:**
```bash
curl -X POST "https://api.epibraingenius.com/api/v1/admin/users/28786b957d75424593bed746316c1e30/upgrade-tier?admin_key=YOUR_ADMIN_KEY" \
  -H "Content-Type: application/json" \
  -d '{"tier": "PRO"}'
```

**Response:**
```json
{
  "id": "28786b957d75424593bed746316c1e30",
  "email": "twinwicksllc@gmail.com",
  "tier": "PRO",
  "message_count": 0,
  ...
}
```

### 2. Get User by ID
**Endpoint:** `GET /api/v1/admin/users/{user_id}`

**Description:** Get detailed user information

**Parameters:**
- `user_id` (path): User ID to retrieve
- `admin_key` (query): Admin API key

**Request:**
```bash
curl "https://api.epibraingenius.com/api/v1/admin/users/28786b957d75424593bed746316c1e30?admin_key=YOUR_ADMIN_KEY"
```

### 3. List All Users
**Endpoint:** `GET /api/v1/admin/users`

**Description:** List all users with pagination

**Parameters:**
- `skip` (query): Number of users to skip (default: 0)
- `limit` (query): Maximum users to return (default: 100)
- `admin_key` (query): Admin API key

**Request:**
```bash
curl "https://api.epibraingenius.com/api/v1/admin/users?skip=0&limit=50&admin_key=YOUR_ADMIN_KEY"
```

**Response:**
```json
[
  {
    "id": "28786b957d75424593bed746316c1e30",
    "email": "twinwicksllc@gmail.com",
    "tier": "PRO",
    ...
  },
  ...
]
```

### 4. Get Platform Statistics
**Endpoint:** `GET /api/v1/admin/stats`

**Description:** Get platform usage statistics

**Parameters:**
- `admin_key` (query): Admin API key

**Request:**
```bash
curl "https://api.epibraingenius.com/api/v1/admin/stats?admin_key=YOUR_ADMIN_KEY"
```

**Response:**
```json
{
  "total_users": 150,
  "free_users": 120,
  "pro_users": 28,
  "enterprise_users": 2,
  "conversion_rate": 20.0
}
```

## How to Upgrade Your Production Account

### Step 1: Generate Admin API Key
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Step 2: Add to Render
1. Go to Render Dashboard → epi-brain-backend → Environment
2. Add: `ADMIN_API_KEY` = your-generated-key-here
3. Save and wait for redeploy

### Step 3: Register on Production Site
1. Visit https://epibraingenius.com
2. Register with twinwicksllc@gmail.com
3. Note your user ID (you'll need it for the upgrade)

### Step 4: Get Your User ID
Option A: Check browser console
1. Log in to https://epibraingenius.com
2. Open browser DevTools → Console
3. Type: `localStorage.getItem('user')`
4. Parse the JSON to find your user ID

Option B: Use admin API
```bash
curl "https://api.epibraingenius.com/api/v1/admin/users?limit=100&admin_key=YOUR_ADMIN_KEY"
```

### Step 5: Upgrade to PRO Tier
```bash
curl -X POST "https://api.epibraingenius.com/api/v1/admin/users/YOUR_USER_ID/upgrade-tier?admin_key=YOUR_ADMIN_KEY" \
  -H "Content-Type: application/json" \
  -d '{"tier": "PRO"}'
```

### Step 6: Verify Upgrade
```bash
curl "https://api.epibraingenius.com/api/v1/admin/users/YOUR_USER_ID?admin_key=YOUR_ADMIN_KEY"
```

Look for `"tier": "PRO"` in the response.

## Security Notes

- **Never share your admin API key**
- **Rotate keys regularly** (every 90 days recommended)
- **Use HTTPS only** for all admin API calls
- **Monitor usage** of admin endpoints
- **Log all admin actions** (implemented in backend)

## Troubleshooting

### Error: "Admin API key not configured"
- Add `ADMIN_API_KEY` to your environment variables
- Restart the backend service

### Error: "Invalid admin API key"
- Verify you're using the correct key
- Check for typos or extra spaces
- Ensure key is properly set in environment variables

### Error: "User not found"
- Verify the user ID is correct
- Use the `/users` endpoint to list all users and find the correct ID
- Ensure the user has registered on the production site

## Example Workflow

```bash
# 1. Generate admin key
ADMIN_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
echo $ADMIN_KEY

# 2. Add to Render environment variables

# 3. Wait for redeploy, then list users
curl "https://api.epibraingenius.com/api/v1/admin/users?admin_key=$ADMIN_KEY"

# 4. Find your user ID in the output
USER_ID="your-user-id-here"

# 5. Upgrade to PRO tier
curl -X POST "https://api.epibraingenius.com/api/v1/admin/users/$USER_ID/upgrade-tier?admin_key=$ADMIN_KEY" \
  -H "Content-Type: application/json" \
  -d '{"tier": "PRO"}'

# 6. Verify upgrade
curl "https://api.epibraingenius.com/api/v1/admin/users/$USER_ID?admin_key=$ADMIN_KEY"

# 7. Get platform stats
curl "https://api.epibraingenius.com/api/v1/admin/stats?admin_key=$ADMIN_KEY"
```

## API Documentation

Full API documentation available at:
https://api.epibraingenius.com/docs

Admin endpoints are under the "Admin" tag in the documentation.