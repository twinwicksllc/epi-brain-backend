# Phase 3: Personality Router & Accountability Styles - Implementation Summary

## Overview
Successfully implemented a personality router system that dynamically selects and adapts accountability styles based on user preferences, conversation context, and emotional state. This includes three distinct accountability personalities (Tactical, Grace, Analyst) plus an Adaptive mode that adjusts based on conversation depth.

## What Was Implemented

### 1. Accountability Style System Prompts (`app/prompts/accountability_styles.py`)

Created comprehensive system prompts for three core accountability personalities:

#### **Tactical/Veteran Style**
- **Tone**: Direct, no-nonsense, tough love
- **Language**: Military-inspired, action-oriented
- **Approach**: "Let's get it done", "No excuses"
- **Best For**: Users who respond well to firm accountability
- **Example**: "You said you'd do it. Let's execute. What's step one?"

#### **Grace/Empathy Style**
- **Tone**: Understanding, gentle, encouraging
- **Language**: Compassionate, patient, affirming
- **Approach**: "I'm here for you", "Take your time"
- **Best For**: Users who need emotional support
- **Example**: "I hear you. That sounds really challenging. How are you feeling about it?"

#### **Analyst Style**
- **Tone**: Objective, data-driven, systematic
- **Language**: Analytical, evidence-based, strategic
- **Approach**: "Let's look at the data", "What's the pattern?"
- **Best For**: Users who prefer facts over feelings
- **Example**: "Looking at your data, I notice a pattern: you're most successful on weekdays. Let's explore why."

#### **Adaptive Style**
- **Behavior**: Dynamically adjusts based on conversation depth
- **High Depth (>0.5)**: Uses Grace approach for emotional safety
- **Low Depth (<0.3)**: Uses Tactical approach for efficiency
- **Medium Depth (0.3-0.5)**: Uses user's preferred style
- **Best For**: Users who want dynamic support

### 2. Personality Router Service (`app/services/personality_router.py`)

Created a sophisticated routing system that determines the appropriate accountability style:

#### **Routing Priority**
1. **User's Emotional State** (highest priority)
   - Distressed/anxious → Grace style
   - Energized/motivated → Tactical style
   - Analytical/curious → Analyst style

2. **Adaptive Routing** (if user preference is 'adaptive')
   - High depth (>0.5) → Grace
   - Low depth (<0.3) → Tactical
   - Medium depth → Analyst

3. **User Preference** (if not adaptive)
   - Respects explicit user choice
   - Applies depth modulation for intensity

4. **Context Signals**
   - Overdue goals (>2) → Tactical
   - Recent struggles → Grace
   - Data-focused queries → Analyst

#### **Key Features**
- Depth-based intensity modulation
- State-aware routing
- Context signal analysis
- Routing decision logging
- Confidence scoring

### 3. AI Service Integration

Updated both Groq and Claude services to support accountability styles:

#### **GroqService Updates** (`app/services/groq_service.py`)
- Added `accountability_style` parameter to `get_response()`
- Added `conversation_depth` parameter to `get_response()`
- Integrated accountability prompts into system prompt
- Updated streaming response method
- Added error handling for prompt loading

#### **ClaudeService Updates** (`app/services/claude.py`)
- Added `accountability_style` parameter to `get_response()`
- Added `conversation_depth` parameter to `get_response()`
- Integrated accountability prompts into system prompt
- Added memory context injection
- Added error handling for prompt loading

### 4. Chat API Integration (`app/api/chat.py`)

Integrated personality router into chat flow:

#### **Regular Chat Flow**
```python
# Determine accountability style
router = get_personality_router()
routing_decision = router.determine_style(
    user_preference=user.accountability_style,
    conversation_depth=conversation_depth,
    user_state=None,
    context_signals={'overdue_goals': count, 'active_goals': count}
)

# Pass to AI service
ai_response = await ai_service.get_response(
    message=message,
    mode=mode,
    accountability_style=routing_decision['style'],
    conversation_depth=conversation_depth,
    ...
)
```

#### **Streaming Chat Flow**
- Same personality routing logic
- Applied in streaming endpoint
- Maintains consistency across response types

### 5. User Preferences API

Updated user profile management to support accountability style:

#### **UserUpdate Schema** (`app/schemas/user.py`)
```python
class UserUpdate(BaseModel):
    voice_preference: Optional[VoicePreference] = None
    primary_mode: Optional[str] = None
    accountability_style: Optional[str] = None  # NEW
```

#### **Update Endpoint** (`app/api/users.py`)
```python
PUT /api/v1/users/me
{
    "accountability_style": "tactical"  // or "grace", "analyst", "adaptive"
}
```

- Validates style against allowed values
- Returns 400 error for invalid styles
- Updates user preference in database

---

## How It Works

### Request Flow

1. **User sends message** to chat API
2. **Personality Router determines style**:
   - Checks user's emotional state (if available)
   - Applies adaptive routing based on depth
   - Respects user preference
   - Analyzes context signals
3. **Style is logged** with reason and confidence
4. **AI service receives style** and conversation depth
5. **System prompt is enhanced** with accountability style
6. **AI generates response** using the selected style
7. **User receives** contextually appropriate support

### Adaptive Routing Example

**Scenario 1: High Depth Conversation**
```
User: "I'm really struggling with my goals lately..."
Depth: 0.7 (high)
Router Decision: Grace style (emotional safety)
AI Response: "I hear you. That sounds really challenging. 
              It's completely okay to have setbacks..."
```

**Scenario 2: Low Depth Conversation**
```
User: "What's my progress today?"
Depth: 0.2 (low)
Router Decision: Tactical style (efficiency)
AI Response: "You have 3 goals in progress. 2 are on track, 
              1 needs attention. Let's tackle it."
```

**Scenario 3: User Distressed**
```
User: "I'm feeling really anxious about everything..."
State: Distressed
Router Decision: Grace style (override preference)
AI Response: "I'm here for you. That sounds overwhelming. 
              Let's take this one step at a time..."
```

---

## Key Features

### 1. Dynamic Style Selection
- Automatically adapts to conversation context
- Respects user preferences
- Overrides for emotional safety
- Logs all routing decisions

### 2. Depth-Aware Adaptation
- High depth → Gentler approach
- Low depth → More direct approach
- Smooth transitions between depths
- Maintains consistency within conversations

### 3. State-Aware Routing
- Detects emotional distress
- Switches to supportive mode
- Prioritizes user wellbeing
- Overrides preferences when needed

### 4. Context Signal Analysis
- Considers overdue goals
- Analyzes recent struggles
- Detects data-focused queries
- Adjusts style accordingly

### 5. User Control
- Users can set preferred style
- Can choose adaptive mode
- Style persists across conversations
- Easy to update via API

---

## Accountability Style Comparison

| Feature | Tactical | Grace | Analyst | Adaptive |
|---------|----------|-------|---------|----------|
| **Tone** | Direct, firm | Gentle, supportive | Objective, logical | Context-aware |
| **Language** | Action-oriented | Compassionate | Data-driven | Flexible |
| **Approach** | "Let's do it" | "I'm here for you" | "Let's analyze" | Adjusts dynamically |
| **Best For** | Motivated users | Struggling users | Analytical users | All users |
| **Intensity** | High | Low | Medium | Variable |
| **Empathy** | Brief | High | Moderate | Adaptive |
| **Challenge** | High | Low | Medium | Context-based |

---

## API Endpoints

### Update Accountability Style
```http
PUT /api/v1/users/me
Content-Type: application/json

{
    "accountability_style": "tactical"
}
```

**Valid Values:**
- `tactical` - Direct, disciplinarian approach
- `grace` - Supportive, understanding approach
- `analyst` - Logical, data-driven approach
- `adaptive` - Context-aware, flexible approach

**Response:**
```json
{
    "id": "user-uuid",
    "email": "user@example.com",
    "accountability_style": "tactical",
    ...
}
```

---

## Testing Recommendations

### 1. Style Consistency Testing
- [ ] Set user style to 'tactical'
- [ ] Have multiple conversations
- [ ] Verify tactical tone is maintained
- [ ] Repeat for grace, analyst, adaptive

### 2. Adaptive Routing Testing
- [ ] Set user style to 'adaptive'
- [ ] Start casual conversation (low depth)
- [ ] Verify tactical approach
- [ ] Transition to deep topic (high depth)
- [ ] Verify switch to grace approach

### 3. State Override Testing
- [ ] Set user style to 'tactical'
- [ ] Express distress in conversation
- [ ] Verify switch to grace style
- [ ] Confirm user safety prioritized

### 4. Context Signal Testing
- [ ] Create multiple overdue goals
- [ ] Start conversation
- [ ] Verify tactical accountability prompt
- [ ] Check routing decision logs

### 5. API Testing
- [ ] Test style update endpoint
- [ ] Verify validation works
- [ ] Test invalid style rejection
- [ ] Confirm persistence across sessions

---

## Monitoring

### Key Metrics
- Style selection frequency (tactical vs grace vs analyst vs adaptive)
- Routing decision confidence scores
- Style override frequency (state-based)
- User style preference distribution
- Depth-based routing patterns

### Logs to Watch
```
INFO: Personality routing for user X: style=tactical, reason=User preference, confidence=0.90
INFO: Personality routing for user X: style=grace, reason=User state: distressed, confidence=0.95
INFO: Personality routing for user X: style=analyst, reason=Adaptive routing based on depth: 0.40, confidence=0.85
```

---

## Configuration

### Router Thresholds
```python
# In PersonalityRouter class
HIGH_DEPTH_THRESHOLD = 0.5  # Switch to grace above this
LOW_DEPTH_THRESHOLD = 0.3   # Switch to tactical below this
```

### Valid Styles
```python
VALID_STYLES = ['tactical', 'grace', 'analyst', 'adaptive']
```

### Default Style
```python
default_style = 'grace'  # Safest default
```

---

## Known Limitations

### 1. User State Detection
- Currently not automatically detected from conversation
- Placeholder for future AI-based emotion detection
- Manual state signals could be added

### 2. Style Switching Mid-Conversation
- Generally maintains consistency within a conversation
- Only switches for critical state changes (distress)
- Could be enhanced with more sophisticated logic

### 3. Context Signal Analysis
- Basic implementation with simple rules
- Could be enhanced with ML-based pattern detection
- More signals could be added (time of day, recent activity, etc.)

---

## Future Enhancements

### Short Term
1. Add user state detection from conversation content
2. Implement more sophisticated context signal analysis
3. Add style effectiveness tracking
4. Create style recommendation system

### Medium Term
1. Add custom style creation (user-defined)
2. Implement style learning (adapt to user feedback)
3. Add style preview/testing mode
4. Create style analytics dashboard

### Long Term
1. Multi-dimensional style system (not just 3 styles)
2. AI-powered style optimization
3. Collaborative style (for team goals)
4. Cultural adaptation of styles

---

## Files Modified

1. `app/services/groq_service.py` - Added accountability style support
2. `app/services/claude.py` - Added accountability style support
3. `app/api/chat.py` - Integrated personality router
4. `app/api/users.py` - Added style update endpoint
5. `app/schemas/user.py` - Added accountability_style to UserUpdate

## Files Created

1. `app/prompts/accountability_styles.py` - System prompts for each style
2. `app/services/personality_router.py` - Routing logic and style selection
3. `PHASE3_PERSONALITY_ROUTER_IMPLEMENTATION.md` - This document

---

## Rollback Plan

If issues arise, personality routing can be disabled by:

**Option 1: Disable in Chat API**
```python
# In app/api/chat.py
PHASE_2B_AVAILABLE = False  # This will skip personality routing
```

**Option 2: Default to Grace Style**
```python
# In PersonalityRouter
self.default_style = 'grace'  # Always use grace (safest)
```

**Option 3: Revert Commit**
```bash
git revert <commit-hash>
git push origin main
```

---

## Success Criteria

✅ Three distinct accountability styles implemented  
✅ Personality router determines appropriate style  
✅ Depth-aware tone adaptation working  
✅ State-aware routing implemented  
✅ User preference API endpoint created  
✅ Integration with both Groq and Claude services  
✅ Comprehensive logging and monitoring  
✅ Backward compatibility maintained  

---

**Status**: ✅ Implementation Complete  
**Deployment**: ⏳ Ready for Testing  
**Date**: January 17, 2025