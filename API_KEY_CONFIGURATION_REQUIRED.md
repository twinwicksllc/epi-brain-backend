# Discovery Mode 503 Error - Root Cause: Missing API Keys

## The Real Problem

The discovery mode is failing because **no AI API keys are configured** in the production environment.

---

## Error Analysis

### Test Results
```bash
$ python test_discovery_detailed.py
```

**Errors Encountered:**

1. **Groq Service Failed:**
   ```
   Groq API error: Connection error.
   ```

2. **Claude Service Failed:**
   ```
   Could not resolve authentication method. Expected either api_key or 
   auth_token to be set. Or for one of the `X-Api-Key` or `Authorization` 
   headers to be explicitly omitted
   ```

3. **Final Error:**
   ```
   All AI services failed. Last error: Error getting AI response: 
   "Could not resolve authentication method..."
   ```

---

## Root Cause

The backend requires AI API keys to function, but none are configured:

- ❌ `GROQ_API_KEY` - Not set
- ❌ `CLAUDE_API_KEY` - Not set
- ❌ `ANTHROPIC_API_KEY` - Not set

**Config File:** `app/config.py`
```python
class Settings(BaseSettings):
    # Groq API
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    
    # Claude/Anthropic API
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    CLAUDE_API_KEY: str = os.getenv("CLAUDE_API_KEY", "")  # Alias
```

Both default to empty strings if not set.

---

## Solution: Configure API Keys

### Option 1: Configure on Render.com

1. Go to your Render dashboard
2. Navigate to the EPI Brain Backend service
3. Go to "Environment" tab
4. Add one of the following environment variables:
   
   **For Groq:**
   ```
   GROQ_API_KEY=your_groq_api_key_here
   ```
   
   **For Claude:**
   ```
   CLAUDE_API_KEY=your_anthropic_api_key_here
   ```

5. Click "Save Changes"
6. Render will automatically redeploy with the new environment variables

### Option 2: Configure via GitHub Secrets (if using GitHub Actions)

```bash
gh secret set GROQ_API_KEY --body "your_groq_api_key_here"
```

### Option 3: Configure via Render CLI

```bash
render env set GROQ_API_KEY your_groq_api_key_here --service your-service-id
```

---

## Getting API Keys

### Groq API Key (Recommended - Free & Fast)
1. Go to https://console.groq.com/
2. Sign up for a free account
3. Navigate to API Keys
4. Create a new API key
5. Copy the key

**Benefits:**
- Free tier available
- Very fast response times
- Good for discovery mode

### Claude API Key
1. Go to https://console.anthropic.com/
2. Sign up for an account
3. Navigate to API Keys
4. Create a new API key
5. Copy the key

**Note:** Claude API is paid but offers high-quality responses.

---

## Code Improvements Added

### API Key Validation
Added validation to check if any API keys are configured before attempting to use AI services:

```python
# Check if any API keys are configured
has_groq_key = bool(settings.GROQ_API_KEY)
has_claude_key = bool(settings.CLAUDE_API_KEY)

if not has_groq_key and not has_claude_key:
    error_msg = "No AI API keys configured. Please set GROQ_API_KEY or CLAUDE_API_KEY environment variables."
    logger.critical(error_msg)
    raise Exception(error_msg)
```

### Better Error Messages
Now provides detailed error messages for each service failure:

```python
errors = []
for service_name, service_class in [('Groq', GroqService), ('Claude', ClaudeService)]:
    try:
        # ... try to get response
    except Exception as e:
        errors.append(f"{service_name}: {str(e)}")
        # ... try next service

if ai_response is None:
    error_detail = f"All AI services failed. Errors: {'; '.join(errors)}"
    logger.critical(error_detail)
    raise Exception(error_detail)
```

**Commit:** `4b9287a` - "Add API key validation and better error messages for AI service failures"

---

## Expected Behavior After Configuration

Once API keys are configured:

### For Unauthenticated Discovery Mode Users:
- ✅ AI services can authenticate with API
- ✅ Responses are generated successfully
- ✅ No 503 errors
- ✅ Discovery mode works perfectly

### Service Priority:
1. **Groq** (tried first - faster, cheaper)
2. **Claude** (fallback if Groq fails)

---

## Verification Steps

After adding API keys and waiting for redeployment:

1. **Test discovery mode:**
   ```bash
   python test_discovery_detailed.py
   ```

2. **Check logs:**
   ```bash
   # Should see:
   # - "Attempting to use Groq service..."
   # - "Successfully got response from Groq service"
   ```

3. **Test in browser:**
   - Go to https://epibraingenius.com
   - Try the discovery chat
   - Should get AI responses

---

## Deployment Status

**Current Status:** Deployment in progress with better error messages

**After Deployment:** Will show clear error message indicating missing API keys instead of generic 503 error.

---

## Summary

The 503 error is NOT a code bug - it's a **configuration issue**. The backend needs at least one AI API key configured to function:

1. ✅ All code fixes are complete
2. ✅ Error handling is improved
3. ❌ **API keys need to be configured in Render**

**Next Step:** Add API keys to Render environment variables and the discovery mode will work!