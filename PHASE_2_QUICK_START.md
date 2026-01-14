# Phase 2 Quick Start Guide

## 5-Minute Testing Checklist

This guide will help you test Phase 2 memory features quickly.

---

## Prerequisites
- ✅ Backend deployed (https://api.epibraingenius.com)
- ✅ Frontend deployed (https://www.epibraingenius.com)
- ✅ User account created

---

## Test 1: Core Variable Collection (2 minutes)

**What to test:** Does AI naturally ask for core information?

**Steps:**
1. Login to epibraingenius.com
2. Click "Personal Friend" mode
3. Send: "Hi, I'm new here!"

**Expected Result:**
The AI should ask:
- What name should I call you?
- What city or area are you located in?
- Do you prefer formal or casual conversations?

**Verify with API:**
```bash
curl -X GET "https://api.epibraingenius.com/api/v1/chat/memory/completion-status" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

Should show:
```json
{
  "completion_percentage": < 100,
  "missing_variables": ["user_profile.name", "user_profile.location", ...]
}
```

---

## Test 2: Active Memory Extraction (2 minutes)

**What to test:** Does AI automatically extract information?

**Steps:**
1. Login to epibraingenius.com
2. Click "Weight Loss Coach" mode
3. Send: "I want to lose 20 pounds by summer. I love hiking but hate the gym."
4. Send 4 more messages (any topic)
5. On the 6th message, memory extraction runs automatically

**Verify with API:**
```bash
curl -X POST "https://api.epibraingenius.com/api/v1/chat/memory/extract" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"conversation_id": "YOUR_CONVERSATION_ID"}'
```

Should show extracted data:
```json
{
  "success": true,
  "extracted_count": > 0,
  "extracted_data": {
    "personality_contexts": {
      "weight_loss_coach": {
        "fitness_goals": [...],
        "exercise_preferences": [...]
      }
    }
  }
}
```

---

## Test 3: Privacy Consent Flow (1 minute)

**What to test:** Does AI ask for consent for sensitive info?

**Steps:**
1. Login to epibraingenius.com
2. Click "Business Mentor" mode
3. Send: "My current revenue is $50K/month and I want to reach $200K."

**Expected Result:**
The AI should ask for permission to remember the revenue numbers.

**Expected Response:**
```
That's an ambitious goal! Would you like me to remember your revenue numbers 
so I can track your progress in future conversations? I won't share this 
information with anyone.

[Yes, remember it] [No, don't store it]
```

---

## API Testing Commands

### Get Memory Completion Status
```bash
curl -X GET "https://api.epibraingenius.com/api/v1/chat/memory/completion-status" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Get Next Priority Variable
```bash
curl -X GET "https://api.epibraingenius.com/api/v1/chat/memory/next-priority-variable" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Trigger Memory Extraction
```bash
curl -X POST "https://api.epibraingenius.com/api/v1/chat/memory/extract" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"conversation_id": "YOUR_CONVERSATION_ID"}'
```

### Get Privacy Settings
```bash
curl -X GET "https://api.epibraingenius.com/api/v1/chat/memory/privacy-settings" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Update Privacy Settings
```bash
curl -X PUT "https://api.epibraingenius.com/api/v1/chat/memory/privacy-settings" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "allow_automatic_extraction": true,
    "consent_for_financial": false
  }'
```

---

## Troubleshooting

### **AI Not Asking for Core Variables**

**Check:**
1. Is `MEMORY_CORE_COLLECTION_ENABLED=True` in backend config?
2. Have you sent fewer than 10 messages?
3. Is conversation depth < 0.6?

**Fix:**
- Start a new conversation
- Send simple messages first
- Don't get into deep topics immediately

### **Memory Not Extracting**

**Check:**
1. Is `MEMORY_AUTO_EXTRACTION_ENABLED=True`?
2. Have you sent at least 5 messages?
3. Is conversation depth > 0.3?

**Fix:**
- Have a meaningful conversation (not just "hi", "ok")
- Wait until message 5, 10, 15 for extraction
- Check API logs for extraction errors

### **Privacy Consent Not Triggering**

**Check:**
1. Is `MEMORY_PRIVACY_CONSENT_ENABLED=True`?
2. Did you mention specific keywords (revenue, income, weight, etc.)?

**Fix:**
- Use explicit phrases like "My revenue is..." or "My weight is..."
- Check if user has already consented to this category

---

## Expected Timeline

- **Message 1-5:** AI asks for core variables
- **Message 5:** First memory extraction runs
- **Message 10:** Second memory extraction runs
- **Every 5 messages:** Continue extraction
- **After 10 messages:** Core variables should be 80%+ complete

---

## What to Look For

### ✅ **Working Correctly:**
- AI asks natural questions about name, location, preferences
- AI remembers what you said in previous messages
- AI references past conversations naturally
- AI asks for consent before storing sensitive info

### ❌ **Not Working:**
- AI doesn't ask any personal questions
- AI doesn't remember anything from previous conversations
- AI explicitly says "I remember you said X" (should be natural)
- Privacy consent never appears

---

## Next Steps After Testing

1. **If tests pass:** Phase 2 is working! 🎉
2. **If tests fail:** Check backend logs on Render
3. **If you want to customize:** Edit `app/config/memory_config.py`

---

## Need Help?

Check the full documentation:
- `PHASE_2_COMPLETE.md` - Complete implementation guide
- `MEMORY_SYSTEM_PHASE_1_COMPLETE.md` - Phase 1 documentation

Or check the code:
- `app/config/memory_config.py` - Variable configuration
- `app/services/core_variable_collector.py` - Core collection logic
- `app/services/active_memory_extractor.py` - Extraction logic
- `app/services/privacy_controls.py` - Privacy logic

---

**Happy Testing!** 🚀