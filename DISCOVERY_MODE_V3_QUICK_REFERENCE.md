# Discovery Mode V3 - Quick Reference Guide

## What Changed?

### 1. **Name Validation: LLM-First**
- **Before:** Length checks (max 40 chars, 4 words)
- **After:** LLM evaluates if input is plausible name
- **Example:** "Skinna marinka..." → LLM says "That's a catchy tune! But what's your name?"

### 2. **Correction Handling**
- **New:** User can correct mistakes ("No, I'm Alexandria, not Alex")
- **LLM detects:** `is_correction=True`
- **Clears previous:** Removes incorrect name
- **Re-prompts:** Asks again without penalty

### 3. **Dynamic Greetings**
- **Before:** "Nice to meet you, [Name]!" (repeated)
- **After:** LLM generates varied, contextual responses
- **Examples:** "Hey, I'm so glad you reached out!" or "That sounds important..."

### 4. **Verification Step**
- **New:** "Did I get that right, [Name]? Or should I call you something else?"
- **Purpose:** Prevent misspelled names from downstream systems

### 5. **Dual Strike Counters** ⭐ KEY CHANGE
```
MAX_HONEST_ATTEMPT_STRIKES = 5  ← User trying but struggling (lenient)
MAX_NON_ENGAGEMENT_STRIKES = 3   ← User clearly wasting time (strict)
```

**Old System:** Single counter, treated all non-engagement equally
**New System:** Differentiates between honest attempts and clear non-engagement

### 6. **Weighted Non-Engagement**
```
Weight 1: Playful but genuine ("Skinna marinka..." on turn 1)
Weight 2: Dismissive ("whatever", "idk")
Weight 3: Clear spam (random keyboard, repeated nonsense)
```

### 7. **Intelligent Failsafe Trigger**
- **Before:** 3 strikes for any non-engagement = failsafe
- **After:** Triggers only when clear non-engagement reaches 3
- **If genuine:** Allows up to 5 attempts even if struggling

---

## Code Changes by File

### 1. `app/prompts/discovery_mode.py`
**What Changed:** Completely rewritten prompt (lines 1-100+)

**Old:** Basic 3-exchange instruction  
**New:** Detailed sections on:
- LLM-first name validation
- Contextual correction logic
- Dynamic greetings
- Verification step
- Signup bridge message

**Example:**
```python
DISCOVERY_MODE_PROMPT = """
...
CONVERSATIONAL NAME VALIDATION (Not Simple Length Checks)

**First Priority: Determine if input is a name, greeting, or nonsense**
...
"""
```

### 2. `app/services/discovery_extraction_service.py` (NEW)
**What:** New service for LLM-driven extraction

**Methods:**
- `validate_and_extract_name()` - Contextual name validation
- `validate_and_extract_intent()` - Intent extraction
- `assess_engagement_quality()` - Judge if user is honest/lazy

**Returns structured data:**
```python
{
    "is_name": bool,
    "name_value": str,
    "is_correction": bool,
    "input_type": str,  # "name" | "greeting" | "nonsense" | etc
    "confidence": float,
    "contextual_response": str
}
```

### 3. `app/api/chat.py`
**Strike Counter Changes:**
```python
# OLD (lines ~180-220)
MAX_DISCOVERY_STRIKES = 3
def _increment_non_engagement_count()
def _reset_non_engagement_count()

# NEW (lines ~90-280)
MAX_HONEST_ATTEMPT_STRIKES = 5
MAX_NON_ENGAGEMENT_STRIKES = 3

def _increment_strike_count(
    conversation, db, strike_weight=1, is_honest_attempt=False
) -> Tuple[int, int]:
    # Returns (non_engagement_strikes, honest_attempt_strikes)

def _should_trigger_failsafe(non_engagement_strikes, honest_attempt_strikes) -> bool:
    # Only triggers if clear non-engagement reaches 3

def _reset_strike_counts(conversation, db):
    # Resets BOTH counters
```

**Failsafe Logic Changes (lines ~503-545):**
```python
if discovery_mode_requested:
    # OLD: Simple engagement check + strike increment
    # NEW: Assess engagement quality with weights
    
    if user_engaged:
        _reset_strike_counts(conversation, db)
    elif invalid_name_detected:
        _increment_strike_count(conversation, db, 
                               strike_weight=1, 
                               is_honest_attempt=False)
    else:
        # Assess if honest attempt or non-engagement
        is_honest = determine_from_context()
        strike_weight = 1 if is_honest else 2
        
        _increment_strike_count(conversation, db,
                               strike_weight=strike_weight,
                               is_honest_attempt=is_honest)
    
    # Refined trigger logic
    failsafe_triggered = _should_trigger_failsafe(
        non_engagement_strikes, honest_attempt_strikes
    )
```

**Context Builder Changes (lines ~348-383):**
```python
def _build_discovery_context(
    metadata,
    trigger_signup_bridge,
    invalid_name_format=False,
    non_engagement_strikes=0,  # NEW parameter
    is_honest_attempt=False     # NEW parameter
) -> Optional[str]:
    # OLD: Just reported what was captured
    # NEW: Reports capture status + strike situation
    
    # Example output:
    """
    <discovery_context>
    ✓ Name Captured: Sarah
    → Next step: Verify the name, then ask about intent

    ⚠️  User not engaging (1/3 strikes).
    → Action: 2 strikes remaining before failsafe. Be direct but warm.
    </discovery_context>
    """
```

---

## User Experience Examples

### Example 1: User with Playful Introduction
```
Turn 1:
  User: "Skinna marinka dinka dink"
  System: Assesses as playful_nonsense, is_honest_attempt=True, weight=1
  Action: honest_attempt_strikes = 1
  EPI: "That's a catchy tune! But I'd love to know what to 
       actually call you. What's your name?"

Turn 2:
  User: "Haha, I'm just joking. I'm Alex."
  System: Detects genuine engagement, resets both counters
  EPI: "I like your sense of humor, Alex! So what brings you here?"
```

### Example 2: User Clearly Not Trying
```
Turn 1:
  User: "hey"
  System: Generic, weight=1, is_honest_attempt=False
  Action: non_engagement_strikes = 1
  EPI: "Hey there! What should I call you?"

Turn 2:
  User: "whatever"
  System: Dismissive, weight=2, is_honest_attempt=False
  Action: non_engagement_strikes = 3 (1 + 2)
  EPI: [FAILSAFE TRIGGERED]
  "I'd love to help... please create an account to continue."
```

### Example 3: User Corrects Name
```
Turn 1:
  User: "I'm Elizabeth"
  System: Captures name, asks for verification
  EPI: "Elizabeth - what a beautiful name! 
       Did I get that right?"

Turn 2:
  User: "Actually, I go by Liz"
  System: Detects correction, is_correction=True
  Action: Clears "Elizabeth", captures "Liz"
  EPI: "Got it, Liz! Thanks for letting me know. 
       So what brings you here today?"
```

---

## Key Configuration Constants

**File:** `app/api/chat.py` (lines ~90-110)

```python
MAX_HONEST_ATTEMPT_STRIKES = 5      # 5 chances if genuinely trying
MAX_NON_ENGAGEMENT_STRIKES = 3       # 3 strikes = failsafe
DISCOVERY_FAILSAFE_MESSAGE = "..."  # Message when failsafe triggers

STRIKE_WEIGHTS = {
    "honest_attempt": 1,            # +1 strike
    "dismissive": 2,                # +2 strikes
    "clear_non_engagement": 3       # +3 strikes (immediate failsafe)
}
```

**To Adjust Behavior:**
1. Make more lenient: Increase `MAX_HONEST_ATTEMPT_STRIKES` to 7
2. Make stricter: Decrease `MAX_NON_ENGAGEMENT_STRIKES` to 2
3. Weight dismissive higher: Change `"dismissive": 3`

---

## Testing

### Run Tests
```bash
python test_discovery_refinement.py
```

### Test Coverage
- ✅ Name validation (simple names, nonsense, greetings)
- ✅ Intent validation (clear intent, vague, non-engagement)
- ✅ Engagement assessment (playful, genuine, dismissive, spam)
- ✅ Correction detection (name changes, clarifications)

---

## Session Memory Structure

**Before:**
```python
conversation.session_memory = {
    "non_engagement_count": 0,
    "invalid_name_count": 0
}
```

**After:**
```python
conversation.session_memory = {
    "non_engagement_strikes": 0,      # Clear non-engagement (max 3)
    "honest_attempt_strikes": 0,      # Genuine attempts (max 5)
    "invalid_name_count": 0           # Invalid name format count
}
```

---

## Logs to Monitor

```
[INFO] User engagement detected, reset strike counts
[INFO] Honest attempt strike 1/5 (weight=1)
[WARNING] Non-engagement strike +2 (now 2/3)
[CRITICAL] Discovery failsafe triggered: non_engagement=3/3
```

---

## Backward Compatibility

✅ **Maintained:**
- Regex-based extraction still used as fallback
- Existing conversation structure unchanged
- Session memory compatible
- API response format unchanged

✅ **Enhanced:**
- Strike counter logic (more intelligent)
- LLM instructions (more detailed)
- Context builder (more information)
- Failsafe logic (more fair)

---

## Performance Impact

### No Negative Impact On:
- ✅ API response times (existing LLM calls)
- ✅ Database queries (same structure)
- ✅ Storage (strike counters are tiny)

### Potential Improvements:
- 📈 Higher conversion rate (less frustration)
- 📈 Better user retention (fair assessment)
- 📈 More honest engagement (lenient with trying users)

---

## Metrics to Track

Monitor these in your dashboard:

1. **Engagement Success Rate**
   - % of users providing name + intent
   - Target: >80%

2. **Honest Attempt Ratio**
   - % of non-engagement from honest attempts
   - Shows if we're being too strict

3. **Failsafe Frequency**
   - How often failsafe triggers
   - Target: <5% of conversations

4. **Average Turns to Capture**
   - Exchanges before getting both fields
   - Target: ≤3 turns

5. **Correction Rate**
   - % of users who correct name/intent
   - Indicates verification step working

---

## Deployment Steps

1. **Code Review** ← You are here
2. **Run test_discovery_refinement.py** - Validate all features
3. **Load test** - Test with realistic user patterns
4. **Monitor metrics** - Track conversion rates for 24 hours
5. **Gather feedback** - Check user happiness
6. **Iterate** - Adjust strike weights based on data

---

## Common Issues & Fixes

### "Failsafe triggers too early"
```python
# Increase lenient threshold
MAX_NON_ENGAGEMENT_STRIKES = 4  # From 3
```

### "Users frustrated with verification step"
```python
# Simplify verification in DISCOVERY_MODE_PROMPT
# Change: "Did I get that right?"
# To: Just ask about intent next
```

### "Too many false positives on non-engagement"
```python
# Increase honest attempt weight
STRIKE_WEIGHTS["honest_attempt"] = 2  # From 1
```

---

**Last Updated:** February 1, 2026  
**Version:** 3.0.0  
**Status:** Implementation Complete - Ready for Testing
