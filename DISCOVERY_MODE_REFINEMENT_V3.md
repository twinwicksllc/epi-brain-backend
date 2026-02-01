# Discovery Mode Refinement - Complete Implementation Guide

**Updated:** February 1, 2026  
**Version:** 3.0.0  
**Status:** Implementation Complete

---

## Overview

This document describes the complete refinement of EPI Brain's Discovery Mode system, moving from simple regex-based extraction to LLM-first contextual validation with intelligent engagement assessment.

### Key Improvements

1. **LLM-First Name Validation** - Contextual understanding instead of length checks
2. **Contextual Correction Logic** - Handles user corrections gracefully
3. **Dynamic Persona-Driven Responses** - No more templated greetings
4. **Verification Step** - Confirmation before moving to intent
5. **Refined Strike Counter** - Differentiates between honest attempts and non-engagement
6. **Intelligent Engagement Assessment** - Weighs user behavior quality

---

## 1. LLM-First Name Validation

### Previous Approach
- Simple regex pattern matching
- Length validation (max 40 chars, 4 words)
- No contextual understanding of what "is a name"

### New Approach

The LLM now determines if input is a **plausible name** by considering:
- Whether it sounds like a name
- Whether it's a greeting ("Hey there")
- Whether it's nonsense ("Skinna marinka...")
- Whether it's a sentence (should not be treated as name)

#### Example Interactions

**Scenario 1: Song/Nonsense**
```
User: "Skinna marinka dinka dink"

Old System: 
  → Would extract if under 40 chars
  → Could result in captured_name: "Skinna marinka dinka dink"

New System:
  → LLM assesses: input_type = "playful_nonsense"
  → is_name = False
  → Responds: "That's a catchy tune! But I'd love to know what to 
    actually call you. What's your name?"
```

**Scenario 2: Casual Introduction**
```
User: "Call me Jordan"

New System:
  → LLM extracts: name_value = "Jordan"
  → is_name = True
  → confidence = 0.95
  → Next: Verify with user before moving to intent
```

**Scenario 3: Sentence Instead of Name**
```
User: "I'm here to improve my mental health and anxiety"

New System:
  → LLM detects: This is a goal statement, not a name
  → is_name = False
  → input_type = "sentence"
  → Responds: "I appreciate your honesty! But what's your name?"
```

### Implementation Details

**File:** `/workspaces/epi-brain-backend/app/services/discovery_extraction_service.py`

Method: `validate_and_extract_name()`

```python
async def validate_and_extract_name(
    user_input: str,
    previous_name: Optional[str] = None,
    conversation_history: Optional[list] = None
) -> Dict[str, any]:
    """
    Returns:
    {
        "is_name": bool,
        "name_value": Optional[str],
        "is_correction": bool,
        "input_type": str,  # "name" | "greeting" | "nonsense" | "sentence" | "playful_nonsense"
        "contextual_response": str,
        "confidence": float
    }
    """
```

---

## 2. Contextual Correction Logic

### Problem Solved
Previously, if a user said "No, that's not my name," the system had no clear way to handle it.

### New Approach

The LLM now:
1. **Detects corrections** - Recognizes when user is correcting a mistake
2. **Clears previous capture** - Removes incorrect name from context
3. **Re-prompts** - Asks for the correct name without moving to intent
4. **Doesn't penalize** - Correction attempts don't count against user

#### Example Interaction

```
User: "I'm Sarah"
EPI: "Got it, Sarah - before I dive in, did I get that right?"

User: "No, actually it's not Sarah. I'm Alexandria"
EPI: 
  [LLM detects: is_correction = True]
  "My apologies for the mix-up, Alexandria! 
   That's a beautiful name. So what brings you here today?"
  [Clears captured_name: "Sarah", replaces with "Alexandria"]
```

### Implementation

The `validate_and_extract_name()` method returns:
```python
{
    "is_correction": bool,  # True if user is correcting previous name
    "contextual_response": "Apology + re-prompt"
}
```

---

## 3. Dynamic Greetings & Warm Persona

### Problem Solved
The system previously used template strings like:
```
"Nice to meet you, [Name]!"
```

This was:
- Repetitive
- Non-conversational
- Didn't adapt to user context

### New Approach

The DISCOVERY_MODE_PROMPT now instructs the LLM to:

1. **Adopt a warm, professional persona**
2. **Generate varied greetings** based on what user says
3. **React naturally** to their input

#### Specific Prompt Instructions

From updated `DISCOVERY_MODE_PROMPT`:

```
DYNAMIC GREETINGS & WARM PERSONA

Eliminate templated responses. Instead, adopt a warm, professional persona 
and generate varied greetings based on what the user actually says:

Good approach:
- "Hey, I'm so glad you reached out today!"
- "That sounds important to you. I'd like to help."
- "I appreciate you being here. What should I call you?"

Avoid:
- "Nice to meet you, [Name]!" (templated)
- Repeating the same opening phrase every time

Let the conversation flow naturally based on what the user reveals.
```

#### Example Interactions

**Natural Response 1:**
```
User: "I'm really struggling with anxiety"
EPI: "That takes courage to share. I'd like to help with that. 
      What should I call you?"
```

**Natural Response 2:**
```
User: "Hi there, just curious about this"
EPI: "Hey! I'm glad you're curious. Let me show you what I can do. 
      First, what's your name?"
```

**Natural Response 3:**
```
User: "I heard you could help with relationships"
EPI: "Absolutely - relationships are so important. I'm excited to chat. 
      What's your name?"
```

### Implementation

The DISCOVERY_MODE_PROMPT (lines 1-50 in `discovery_mode.py`) contains detailed instructions for the LLM about persona and tone.

---

## 4. Verification Step (Confirmation)

### Problem Solved
Without verification, misspelled names could be captured and passed downstream.

### New Approach

**After capturing a name, the system now:**

1. Pauses before asking about intent
2. Asks for verification: "Did I get that right, [Name]? Or should I call you something else?"
3. Waits for confirmation before proceeding

### Implementation

The DISCOVERY_MODE_PROMPT includes:

```
VERIFICATION STEP (CRITICAL)

After capturing a name, DO NOT immediately ask about intent.
PAUSE and confirm first:

Example: "Did I get that right, [Name]? Or should I call you something else?"

This builds trust and prevents incorrect name capture downstream.
```

#### Exchange Sequence

```
Turn 1:
User: "My name is Elizabeth"
EPI: "Elizabeth - that's a wonderful name! 
     Before I ask what brings you here, did I get that right?"

Turn 2:
User: "Yes, that's correct"
EPI: "Perfect! So what brings you here today?"

--- OR ---

Turn 2:
User: "Actually, I go by Liz"
EPI: "Got it, Liz! I appreciate the clarification. 
     So what brings you here today?"
```

---

## 5. Refined Strike Counter Logic

### Previous Approach
- Single counter: "non_engagement_strikes"
- Treated all non-engagement equally
- Hard threshold: 3 strikes = failsafe

### New Approach

**Two separate counters with different weights:**

1. **Non-Engagement Strikes** (Strict - 3 strikes max)
   - Clear time-wasting, spam, or dismissive behavior
   - Each strike can have weight 1-3
   - Examples:
     - "whatever" (weight: 2)
     - Random keyboard spam (weight: 3)
     - Consistent refusal to engage (weight: 2-3)

2. **Honest Attempt Strikes** (Lenient - 5 strikes allowed)
   - User is genuinely trying but struggling
   - User made playful but honest attempt
   - Examples:
     - Song/joke on turn 1 (weight: 1, but honest)
     - "I'm not sure what to say" (weight: 1, but honest)
     - Multiple attempts that seem genuine

### Configuration

```python
MAX_NON_ENGAGEMENT_STRIKES = 3    # Strict threshold
MAX_HONEST_ATTEMPT_STRIKES = 5    # Lenient threshold

STRIKE_WEIGHTS = {
    "honest_attempt": 1,           # Playful or struggling
    "dismissive": 2,               # Dismissive but recoverable
    "clear_non_engagement": 3      # Clearly wasting time or spam
}
```

### Strike Increment Logic

```python
def _increment_strike_count(
    conversation: Conversation,
    db: Session,
    strike_weight: int = 1,
    is_honest_attempt: bool = False
) -> Tuple[int, int]:
    """
    Returns: (non_engagement_strikes, honest_attempt_strikes)
    """
    if is_honest_attempt:
        # User is trying but struggling
        honest_attempt_strikes += 1
        # More chances allowed (5 max)
    else:
        # User is not engaging
        non_engagement_strikes += strike_weight  # Can add 1-3
        # Stricter threshold (3 max)
```

### Failsafe Trigger Logic

```python
def _should_trigger_failsafe(
    non_engagement_strikes: int,
    honest_attempt_strikes: int
) -> bool:
    # Trigger ONLY when clear non-engagement threshold reached
    if non_engagement_strikes >= MAX_NON_ENGAGEMENT_STRIKES:
        return True
    
    # Don't trigger if user is honestly trying
    return False
```

### Example Scenarios

**Scenario 1: User is Playful but Honest**
```
Turn 1:
User: "Skinna marinka dinka dink"
Assessment: playful_nonsense, honest_attempt=True, strike_weight=1
Action: Increment honest_attempt_strikes to 1
LLM Response: "That's a catchy tune! But what's your name?"

Turn 2:
User: "I'm just joking, my name is Alex"
Assessment: genuine_attempt
Action: Reset all strike counts
LLM Response: "Ha! I like your sense of humor, Alex! 
              So what brings you here?"
```

**Scenario 2: User is Clearly Wasting Time**
```
Turn 1:
User: "Hello"
Assessment: generic, not honest attempt attempt=False, weight=1
Action: non_engagement_strikes = 1

Turn 2:
User: "whatever"
Assessment: dismissive, is_honest_attempt=False, weight=2
Action: non_engagement_strikes = 3 (1 + 2)

Turn 3:
[Failsafe triggers]
EPI: "I'd love to help you... please create an account to continue"
```

**Scenario 3: User is Struggling but Genuine**
```
Turn 1:
User: "um... I don't know what to say"
Assessment: struggling, is_honest_attempt=True, weight=1
Action: honest_attempt_strikes = 1

Turn 2:
User: "I'm not really sure how this works"
Assessment: genuine_confusion, is_honest_attempt=True
Action: Reset non_engagement_strikes, keep honest_attempt_strikes=1
LLM Response: "No worries! I'll walk you through this. 
              What should I call you?"

Turn 3:
User: "I'm Jamie"
Assessment: genuine_attempt
Action: Reset all strikes
LLM Response: "Jamie, wonderful! So what brings you here?"
```

### Implementation Files

**Primary:** `/workspaces/epi-brain-backend/app/api/chat.py`

Key functions:
- `_increment_strike_count()` - Lines ~220
- `_should_trigger_failsafe()` - Lines ~260
- `_reset_strike_counts()` - Lines ~275
- Discovery failsafe logic - Lines ~503-545

---

## 6. Intelligent Engagement Assessment

### New Service

**File:** `/workspaces/epi-brain-backend/app/services/discovery_extraction_service.py`

**Method:** `assess_engagement_quality()`

```python
async def assess_engagement_quality(
    user_input: str,
    conversation_turn: int = 1,
    previous_inputs: Optional[list] = None
) -> Dict[str, any]:
    """
    Assess whether user is genuinely engaged or clearly wasting time.
    
    Returns:
    {
        "is_engaged": bool,
        "is_honest_attempt": bool,
        "is_non_engagement": bool,
        "strike_weight": 1-3,
        "engagement_pattern": str,  # "genuine" | "playful" | "dismissive" | 
                                    # "clearly_not_trying" | "spam"
        "recommendation": str
    }
    """
```

### Engagement Patterns

| Pattern | Weight | Context | Action |
|---------|--------|---------|--------|
| genuine | 0 | "I'm Alex. Help with anxiety" | Reset strikes, proceed |
| playful | 1 | "Skinna marinka..." on turn 1 | +1 honest attempt, respond contextually |
| dismissive | 2 | "whatever", "idk", "maybe?" | +2 non-engagement, be direct |
| clearly_not_trying | 3 | Random keyboard spam repeatedly | +3 non-engagement, trigger failsafe |
| spam | 3 | Repeated nonsense across turns | Immediate failsafe |

### Key Features

1. **Context-Aware** - Considers conversation turn and history
2. **Pattern Recognition** - Learns from user's input pattern
3. **Weighted Assessment** - Different behaviors have different weights
4. **Recommendation System** - Provides specific next steps

---

## 7. Updated Discovery Context Builder

### File
`/workspaces/epi-brain-backend/app/api/chat.py` - Function `_build_discovery_context()`

### Purpose
Creates instruction block for the LLM with:
- What's been captured
- What strike situation we're in
- How to respond

### Example Output

```
<discovery_context>
✓ Name Captured: Sarah
→ Next step: Verify the name, then ask about intent

⚠️  User not engaging (1/3 strikes).
→ Action: 2 strike(s) remaining before failsafe triggers. Be direct but warm.
</discovery_context>
```

---

## 8. Strike Counter Updates in Session Memory

### Session Memory Structure

```python
conversation.session_memory = {
    "non_engagement_strikes": 0,      # Clear non-engagement (max 3)
    "honest_attempt_strikes": 0,      # Genuine attempts (max 5)
    "invalid_name_count": 0,          # Invalid name format count
}
```

### Update Points

1. **On Engagement** → Reset both strike counters
2. **On Invalid Name** → Increment invalid_name_count
   - If reaches 2 → Increment non_engagement_strikes
3. **On Non-Engagement** → Increment non_engagement_strikes with weight
4. **On Honest Attempt** → Increment honest_attempt_strikes
5. **On Signature Weakness** → Don't penalize if they're trying

---

## 9. Integration with Chat API

### Modified Endpoints

**POST /api/v1/chat/message**

**Changed Logic:**

1. Extract metadata using existing regex (fallback)
2. For discovery mode, apply refined strike logic:
   ```python
   if discovery_mode_requested:
       # Assess engagement quality
       user_engaged = _check_discovery_engagement(discovery_metadata)
       
       if user_engaged:
           _reset_strike_counts(conversation, db)
       else:
           # Assess quality and determine weight
           is_honest = determine_honest_attempt(message)
           strike_weight = 1 if is_honest else 2
           
           _increment_strike_count(
               conversation,
               db,
               strike_weight=strike_weight,
               is_honest_attempt=is_honest
           )
       
       # Check if failsafe should trigger
       failsafe_triggered = _should_trigger_failsafe(
           non_engagement_strikes,
           honest_attempt_strikes
       )
   ```

3. Build context with strike information
4. Pass context to LLM as system instruction

---

## 10. Testing

### Test File
`/workspaces/epi-brain-backend/test_discovery_refinement.py`

### Test Coverage

1. **Name Validation Tests**
   - Simple names
   - Playful nonsense
   - Mixed inputs
   - Greetings
   - Casual introductions

2. **Intent Validation Tests**
   - Clear intent statements
   - Vague responses
   - Detailed intent
   - Non-engagement

3. **Engagement Assessment Tests**
   - Playful nonsense on turn 1
   - Genuine attempts
   - Dismissive responses
   - Clear spam

4. **Correction Detection Tests**
   - Name corrections
   - Clarifications
   - User feedback

### Running Tests

```bash
python test_discovery_refinement.py
```

---

## 11. Configuration Constants

**File:** `/workspaces/epi-brain-backend/app/api/chat.py` (Lines 90-110)

```python
# Refined strike counter configuration
MAX_HONEST_ATTEMPT_STRIKES = 5  # User is trying but struggling
MAX_NON_ENGAGEMENT_STRIKES = 3   # User is clearly wasting time

DISCOVERY_FAILSAFE_MESSAGE = (
    "I'd love to help you with that! To unlock my full capabilities and "
    "move beyond our initial discovery, let's get your account set up first."
)

STRIKE_WEIGHTS = {
    "honest_attempt": 1,      # Playful but genuine
    "dismissive": 2,          # Dismissive but recoverable
    "clear_non_engagement": 3 # Clear time-wasting
}
```

### Tuning

To adjust behavior:

1. **More lenient with honest attempts:**
   ```python
   MAX_HONEST_ATTEMPT_STRIKES = 7  # More chances
   ```

2. **Stricter with non-engagement:**
   ```python
   MAX_NON_ENGAGEMENT_STRIKES = 2  # Less tolerance
   ```

3. **Adjust weights per behavior:**
   ```python
   STRIKE_WEIGHTS = {
       "honest_attempt": 1,        # No change
       "dismissive": 3,            # Stricter
       "clear_non_engagement": 3   # Same
   }
   ```

---

## 12. Backward Compatibility

### Maintained
- Regex-based extraction still used as fallback
- Existing conversation structure unchanged
- Session memory compatible
- API response format unchanged

### Enhanced
- Strike counter logic (dual counters instead of single)
- LLM instructions (more detailed)
- Context builder (more information)
- Failsafe triggers (more intelligent)

---

## 13. Monitoring & Logging

### Key Logs to Watch

```
[INFO] Discovery extraction: validating name "Sarah"
[INFO] User engagement detected, reset strike counts for conversation {id}
[INFO] Honest attempt strike 1/5 (weight=1) for conversation {id}
[WARNING] Non-engagement strike +2 (now 2/3) for conversation {id}
[CRITICAL] Discovery failsafe triggered for conversation {id}: non_engagement=3/3
```

### Metrics to Track

1. **Engagement Success Rate** - % of users who provide name + intent
2. **Honest Attempt Ratio** - % of non-engagement that's honest attempts
3. **Failsafe Frequency** - How often failsafe triggers
4. **Average Turns to Capture** - Exchanges before getting name + intent
5. **Correction Rate** - % of users who correct name/intent

---

## 14. Future Enhancements

1. **Machine Learning Integration**
   - Train model on real user patterns
   - Improve engagement assessment
   - Personalize strike weights per demographic

2. **Context Preservation**
   - Remember user patterns across sessions
   - Adjust approach based on history
   - Recognize returning users

3. **A/B Testing**
   - Test different persona styles
   - Optimize prompt wording
   - Measure conversion impacts

4. **Analytics Dashboard**
   - Real-time strike counter insights
   - Engagement pattern visualization
   - Conversion funnel tracking

---

## Summary of Changes

| Component | Before | After |
|-----------|--------|-------|
| Name Validation | Regex + length check | LLM-first contextual |
| Greetings | Template strings | Dynamic persona |
| Corrections | No handling | Full contextual support |
| Strike Logic | Single counter (3 max) | Dual counters (3 strict, 5 lenient) |
| Engagement Assessment | Binary (engaged/not) | Weighted quality assessment |
| LLM Instructions | Basic | Detailed with strike info |
| Failsafe Trigger | Simple threshold | Intelligent assessment |

---

## Deployment Checklist

- [x] Updated DISCOVERY_MODE_PROMPT with new instructions
- [x] Created DiscoveryExtractionService with LLM validation
- [x] Implemented dual strike counter logic
- [x] Updated _build_discovery_context() function
- [x] Updated chat.py with refined failsafe logic
- [x] Added engagement assessment logic
- [x] Created comprehensive test suite
- [ ] Run test suite and validate
- [ ] Load test with realistic user patterns
- [ ] Monitor discovery conversion rates
- [ ] Gather user feedback
- [ ] Iterate based on metrics

---

**Status:** Ready for Testing and Deployment  
**Next Steps:** Run test_discovery_refinement.py to validate all functionality
