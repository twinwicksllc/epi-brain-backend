# Quick Setup Instructions

## Your Admin API Key
```
jqdH7SonlkQl0FlQP3_D_eyPryR8VDHOSvcl5enFGyo
```

## Step 1: Add Admin API Key to Render

1. Go to: https://dashboard.render.com
2. Click on: `epi-brain-backend`
3. Go to: Settings → Environment
4. Click: "Add New Variable"
5. Enter:
   - Key: `ADMIN_API_KEY`
   - Value: `jqdH7SonlkQl0FlQP3_D_eyPryR8VDHOSvcl5enFGyo`
6. Click: "Save"
7. Wait for redeploy (2-3 minutes)

## Step 2: Register on Production Site

1. Go to: https://epibraingenius.com
2. Click: "Register"
3. Enter your email: twinwicksllc@gmail.com
4. Create a password
5. Click: "Register"

## Step 3: Get Your User ID

**Option A - Browser Console (Recommended):**
1. Log in to https://epibraingenius.com
2. Press F12 to open DevTools
3. Go to "Console" tab
4. Type: `JSON.parse(localStorage.getItem('user')).id`
5. Copy the user ID that appears

**Option B - Admin API (after admin key is configured):**
```bash
curl "https://api.epibraingenius.com/api/v1/admin/users?admin_key=jqdH7SonlkQl0FlQP3_D_eyPryR8VDHOSvcl5enFGyo"
```
Find your user ID in the list.

## Step 4: Upgrade Your Account to PRO Tier

Once you have your user ID, run this command in your terminal:

```bash
curl -X POST "https://api.epibraingenius.com/api/v1/admin/users/YOUR_USER_ID/upgrade-tier?admin_key=jqdH7SonlkQl0FlQP3_D_eyPryR8VDHOSvcl5enFGyo" \
  -H "Content-Type: application/json" \
  -d '{"tier": "PRO"}'
```

Replace `YOUR_USER_ID` with the actual user ID you found in Step 3.

## Step 5: Verify Your Upgrade

```bash
curl "https://api.epibraingenius.com/api/v1/admin/users/YOUR_USER_ID?admin_key=jqdH7SonlkQl0FlQP3_D_eyPryR8VDHOSvcl5enFGyo"
```

Look for `"tier": "PRO"` in the response.

## Summary

1. ✅ Admin API Key generated: `jqdH7SonlkQl0FlQP3_D_eyPryR8VDHOSvcl5enFGyo`
2. ⏳ Add to Render environment variables
3. ⏳ Register on https://epibraingenius.com
4. ⏳ Get your user ID from browser console
5. ⏳ Use the upgrade command to get PRO tier
6. ⏳ Enjoy unlimited messages!

## Need Help?

If you need help with any step, let me know and I can guide you through it!