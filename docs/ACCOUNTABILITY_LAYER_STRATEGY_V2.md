# Clarity & Accountability Layer - Strategic Approach V2

## Vision Statement

Transform EPI Brain from a passive conversational AI into an **intelligent, state-aware life partner** that helps users achieve their goals through gritty, realistic support. Not "toxic positive" but a **veteran mentor** - disciplined, authentic, and adaptive.

## Core Philosophy: "Intelligent, Compassionate Accountability"

> "A mentor doesn't just compliment. They check in, set milestones, call out misses, and help you replicate wins."

**Key Principles:**
1. **Supportive but Disciplined** - High expectations with genuine care
2. **Gritty & Realistic** - Not toxic positive, not overly pessimistic
3. **Deep Emotional Intelligence** - Handle complex emotions without being prying
4. **Contextually Adaptive** - Adjust tone based on conversation depth and user state
5. **State-Aware Routing** - Respect user's mental state, don't just follow scripts

---

## Technical Architecture

### 1. Persona Router System

**Purpose**: Route requests through appropriate personality wrapper based on mode, user preferences, and current state.

**Flow:**
```
User Request 
  ↓
Persona Router Function
  ↓
┌─────────────────────────────────────┐
│ Check: User's Active Mode           │
│ Check: User's Accountability Style │
│ Check: Current Mental State (optional) │
│ Check: Conversation Depth          │
└─────────────────────────────────────┘
  ↓
Select Personality Wrapper
  ↓
Wrap System Prompt + User Input
  ↓
Send to LLM
  ↓
Response
```

**Components:**
- **Mode Router**: Routes to mode-specific personality (Personal Friend, Weight Loss Coach, etc.)
- **Accountability Style Router**: Routes to style-specific wrapper (Tactical/Veteran, Grace/Empathy, Analyst)
- **State-Aware Adapter**: Overrides based on sentiment/mood detection
- **Depth Adapter**: Adjusts tone based on conversation depth (deep = more grounded; surface = more energetic)

### 2. State-Aware Backend

**User Metadata (users table):**
```sql
response_preference TEXT -- 'tactical_veteran', 'grace_empathy', 'analyst', or 'adaptive'
accountability_style TEXT -- chosen default style
sentiment_override BOOLEAN -- allow state-aware overrides
depth_sensitivity BOOLEAN -- allow depth-based tone changes
```

**Sentiment Trigger System:**
- Analyze user input sentiment before routing
- If discouraged/stressed → temporarily inject "Grace-Giver" logic
- Prevent burnout while maintaining accountability
- Revert to chosen style after recovery

**Depth Awareness System:**
- Leverage existing depth scoring system
- Deep conversations → calming, grounding tone
- Surface/congratulatory → high energy, celebratory tone
- Learn from wins → analyze patterns for replication

---

## Accountability Styles

### 1. Tactical/Veteran (Disciplinarian)
**Tone**: Direct, no-nonsense, military-style mentor
**When Used**: User chooses "Tactical/Veteran" style
**Example Approach:**
> "You missed your gym sessions this week. That's three days. What's the plan for tomorrow to get back on track? I'm not asking if you want to, I'm asking when you're going."

**Strengths**: Clear accountability, avoids excuses, high expectations
**Best For**: Business Mentor, Weight Loss Coach (when user wants discipline)

### 2. Grace/Empathy (Supportive)
**Tone**: Understanding, encouraging, positive focus on setbacks
**When Used**: User chooses "Grace/Empathy" style OR sentiment override triggered
**Example Approach:**
> "I know this week has been tough. Let's look at what went well - you got two workouts in. That's progress. What's one small thing we can do tomorrow?"

**Strengths**: Builds confidence, prevents burnout, maintains motivation
**Best For**: Christian Companion, Personal Companion, Psychology Expert

### 3. Analyst (Logical/Pragmatic)
**Tone**: Data-driven, statistical, "nerd speak"
**When Used**: User chooses "Analyst" style
**Example Approach:**
> "Looking at your tracking data: You're at 85% completion rate this month. One missed session is a single statistical outlier - 1.5 sigma deviation - not a pattern unless it becomes recurrent. Probability of maintaining streak: 73% if you complete tomorrow's session."

**Strengths**: Objective perspective, removes emotion from setbacks, appeals to logical thinking
**Best For**: Weight Loss Coach, Business Mentor (data-driven users)

---

## Semantic Memory with pgvector

### Purpose: Cross-Conversation Context Awareness

**Current Problem:** Every conversation starts fresh → "How can we help you today?"

**With Semantic Memory:** AI remembers → "Last time we talked, you were worried about..."

### Implementation

**Database Schema:**
```sql
-- Add to existing setup
CREATE TABLE semantic_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    mode TEXT, -- which mode this memory is relevant to
    embedding vector(1536), -- pgvector embedding
    content TEXT, -- the memory text
    importance_score FLOAT, -- 0.0-1.0
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP -- optional, for temporary memories
    last_accessed TIMESTAMP,
    access_count INT DEFAULT 0
);

CREATE INDEX ON semantic_memories USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_semantic_memories_user_mode ON semantic_memories(user_id, mode);
```

**Memory Extraction Service:**
```python
class SemanticMemoryExtractor:
    """Extract important facts from conversations for semantic storage"""
    
    def extract_memories(self, conversation: Conversation, messages: List[Message]) -> List[SemanticMemory]:
        """Analyze conversation and extract key facts"""
        # Use AI to identify important information
        # Generate embeddings with OpenAI/Claude API
        # Store in pgvector
        pass
    
    def retrieve_relevant_memories(self, user_id: UUID, mode: str, current_input: str) -> List[SemanticMemory]:
        """Find semantically similar memories for context"""
        # Generate embedding for current input
        # Search pgvector for similar memories
        # Return top N memories
        pass
```

**Memory Retrieval Flow:**
```python
# In Persona Router before sending to LLM
current_input = user_message

# Get relevant semantic memories
relevant_memories = semantic_memory_extractor.retrieve_relevant_memories(
    user_id=current_user.id,
    mode=current_mode,
    current_input=current_input
)

# Build context
context_builder = f"""
User Context:
{format_memories_for_prompt(relevant_memories)}

Current Input:
{current_input}
"""

# Send to LLM with context
```

**Modes with Semantic Memory:**
- ✅ Personal Friend - Remember personal details, relationships, life events
- ✅ Christian Companion - Remember spiritual journey, prayer requests, faith questions
- ✅ Psychology Expert - Remember patterns, triggers, progress in therapy topics
- ✅ Business Mentor - Remember business goals, wins, challenges, team dynamics
- ✅ Weight Loss Coach - Remember food preferences, exercise habits, setbacks
- ✅ Kids Mode - Remember interests, school activities, achievements (simplified)

**Modes WITHOUT Semantic Memory:**
- ❌ Student Tutor - Each session should be fresh learning
- ❌ Business Training - Each training module independent

**Memory Privacy:**
- Per-mode isolation (memories don't leak between modes)
- User can delete all memories for a specific mode
- Memories expire after configurable period (default: 90 days, extendable)
- Sensitive topics (health, finances) require explicit consent

---

## Scheduled Check-ins with pg_cron

### Purpose: Proactive Accountability Beyond Chat Sessions

**Implementation:**
```sql
-- Schedule check-in reminders
SELECT cron.schedule(
    'weight-loss-evening-checkin',
    '0 19 * * *', -- 7 PM daily
    $$SELECT notify_user_weight_loss_checkin()$$
);

-- Schedule pulse checks
SELECT cron.schedule(
    'weekly-pulse-check',
    '0 9 * * 1', -- 9 AM Monday
    $$SELECT notify_user_weekly_pulse()$$
);
```

**Check-in Types:**

1. **Time-Based Triggers**
   - Weight Loss Coach → Evening check-ins (dinner/late night)
   - Business Mentor → Monday morning planning
   - Personal Friend → Weekend reflection

2. **Pattern-Based Triggers**
   - Missed 3 days in a row → "Hey, haven't seen you..."
   - Streak of 7 days → "Great job! Keep it going!"
   - Goal deadline approaching → "How's it going with..."

3. **Context-Based Triggers**
   - Calendar event (integration) → "How did the meeting go?"
   - Weather data (integration) → "Rainy day, perfect for that indoor workout"

**Notification Channels:**
- **Twilio** - SMS/text messages
- **WhatsApp** - Rich text, images, interactive buttons
- **Email** - Detailed weekly summaries
- **In-App Push** - Mobile notifications

**Check-in Content Examples:**

**Weight Loss Coach (Evening, WhatsApp):**
```
Hey! 👋

Quick check-in: How's dinner going? 
🥗 Staying on track?
🍕 Or did the pizza win? 

No judgment either way - just tracking. 
Reply "👍" for healthy, "😐" for meh, "🍕" for slip-up.
We'll adjust tomorrow's plan accordingly.
```

**Business Mentor (Monday Morning, Email):**
```
Monday Morning Planning 📅

Last week you closed 2 deals - solid work! 🎯

Top priorities this week:
1. Follow up with [Client X] (won mentioned they were interested)
2. Prepare for [Meeting Y] (pattern: you do better when you prep)
3. Continue outreach (15 calls/day = 75 calls/week)

What's your game plan?
```

**Personal Friend (Weekend, In-App):**
```
Weekend reflection time! 🌅

How was your week? Anything you're proud of?
Anything we should work through together?
I'm here for the wins and the losses. 💪
```

---

## Psychology Expert with CBT Principles

### Purpose: Therapeutic-level support without legal liability

**Disclaimer System:**
```
I'm an AI companion, not a licensed therapist. 
While I can use CBT techniques to help you work through challenges,
for serious mental health concerns, please consult a professional.
```

**CBT Techniques Implemented:**

1. **Cognitive Restructuring**
   - Identify negative thought patterns
   - Challenge irrational beliefs
   - Replace with balanced thoughts
   - Example: "I always fail" → "I've had setbacks, but also successes"

2. **Behavioral Activation**
   - Identify activities that improve mood
   - Schedule pleasant/meaningful activities
   - Track mood vs. activity patterns
   - Break avoidance cycles

3. **Thought Records**
   - Capture situations, thoughts, emotions
   - Identify cognitive distortions
   - Generate alternative thoughts
   - Track progress over time

4. **Exposure Hierarchy**
   - Rank feared situations by difficulty
   - Gradual exposure with support
   - Track anxiety levels
   - Celebrate progress

5. **Problem-Solving Skills**
   - Define problems clearly
   - Generate multiple solutions
   - Evaluate pros/cons
   - Implement and review

**Implementation Example:**

```
User: "I'm feeling overwhelmed at work. Everyone hates me."

Psychology Expert:
"I hear you're feeling overwhelmed. Let's work through this together using some CBT techniques.

1. **Fact-check**: You mentioned 'everyone hates me' - can you think of any evidence that contradicts this? Any coworkers who've been supportive?

2. **Cognitive distortion**: That sounds like 'all-or-nothing thinking' - when we see things in black and white without gray areas.

3. **Balanced thought**: Could it be that some people are stressed/distracted rather than specifically disliking you?

4. **Action plan**: What's one small thing we could do this week to improve a work relationship?"

Would you like to dig deeper into any of these?
```

**Safety Layers:**
- Detect high-risk keywords (suicide, self-harm, abuse)
- Provide crisis resources immediately
- Encourage professional help
- Never diagnose or prescribe

---

## Conversation Depth & Tone Adaptation

### Leverage Existing Depth Scoring System

**Current System:**
- `depth` field in conversations (0.0 to 1.0)
- `last_depth_update` timestamp
- `depth_enabled` boolean

**Enhanced with Tone Adaptation:**

**High Depth (0.7+):**
- Tone: Calming, grounding, reflective
- Pacing: Slower, more thoughtful
- Examples:
  - "Let's sit with that for a moment..."
  - "That's a lot to process. Take your time."
  - "I want to make sure I understand this fully..."

**Medium Depth (0.3-0.7):**
- Tone: Supportive, engaged, conversational
- Pacing: Normal conversational pace
- Examples:
  - "That's interesting - tell me more."
  - "How did that make you feel?"
  - "What's your take on that?"

**Low Depth (<0.3):**
- Tone: Energetic, congratulatory, action-oriented
- Pacing: Quick, motivating
- Examples:
  - "That's amazing! 🎉"
  - "Let's get this done!"
  - "What's next on the agenda?"

**Dynamic Tone Shifting:**

**Business Mentor Example:**
```
Surface (Win): 
"INCREDIBLE! You closed that deal! 🚀 We need to figure out exactly what you did so we can replicate this EVERY TIME!"

Deep (Challenge):
"Let me get this straight - you're feeling burnt out because you're taking on too much. I get that. Let's ground this in reality: What's actually on your plate, and what can we delegate?"
```

**Weight Loss Coach Example:**
```
Surface (Success):
"Yes! 5 pounds down! Keep doing what you're doing! 💪"

Deep (Emotional struggle):
"I hear you. Food isn't just about nutrition - it's emotional. And that's okay. Let's talk about what's going on emotionally right now, no judgment."
```

---

## Implementation Phases (Revised)

### Phase 1: Foundation (Week 1-2)
**Database Schema:**
- Goals, check-ins, progress tracking tables
- Semantic memories table with pgvector
- User metadata for accountability styles
- Scheduled jobs table

**Core Services:**
- Goal management service
- Check-in scheduler
- Progress tracker
- Semantic memory extractor (basic)
- Semantic memory retriever

**Infrastructure:**
- Set up pgvector extension
- Configure pg_cron
- Set up Twilio/WhatsApp (or API endpoints for later)

### Phase 2: Persona Router (Week 3-4)
**Components:**
- Mode-specific personality wrappers
- Accountability style wrappers (Tactical, Grace, Analyst)
- State-aware adapter
- Depth-aware adapter

**Features:**
- Dynamic personality routing
- Sentiment-based overrides
- Depth-based tone adjustment
- Context building from semantic memory

### Phase 3: Semantic Memory Integration (Week 5-6)
**Features:**
- Memory extraction from conversations
- Semantic search and retrieval
- Mode-specific memory isolation
- Memory importance scoring
- Context building for LLM prompts

**Modes with Memory:**
- Personal Friend
- Christian Companion
- Psychology Expert
- Business Mentor
- Weight Loss Coach
- Kids Mode

### Phase 4: Psychology Expert CBT (Week 7-8)
**Features:**
- CBT technique library
- Thought record system
- Behavioral activation tracking
- Exposure hierarchy builder
- Safety layer for high-risk topics

### Phase 5: Scheduled Check-ins (Week 9-10)
**Features:**
- pg_cron scheduling
- Time-based triggers
- Pattern-based triggers
- Multi-channel notifications (SMS, WhatsApp, email, push)
- Check-in content templates per mode

### Phase 6: Advanced Features (Week 11-12)
**Features:**
- ML-based pattern recognition
- Win replication analysis
- Predictive intervention
- Advanced analytics
- A/B testing framework

---

## Success Metrics

### User Engagement:
- Semantic memory hit rate (memories found relevant)
- Check-in response rate
- Goal achievement rate
- Depth-adjusted conversation quality scores

### User Satisfaction:
- Context awareness score ("Does the AI remember important things?")
- Accountability helpfulness score
- Tone appropriateness score
- Overall NPS

### Business Impact:
- User retention (users with semantic memories vs. without)
- Premium conversion (accountability features as premium tier)
- Check-in completion rates
- Goal milestone achievement rates

---

## Privacy & Ethics

### What We Collect:
- Goals, progress, check-ins
- Semantic memories (extracted facts from conversations)
- Behavioral patterns
- Emotional trends (sentiment analysis)

### What We Don't Collect:
- Biometric data (unless explicitly connected by user)
- Cross-platform data without consent
- Sharing with third parties

### Privacy Features:
- Mode-specific memory isolation
- User control over memory retention
- Export/delete all semantic memories
- Transparent AI decision-making
- CBT disclaimer (Psychology Expert mode)
- Crisis resources for high-risk topics

---

## Competitive Advantages

1. **State-Aware Routing**: Respects mental state, not just mode
2. **Semantic Memory with pgvector**: True context awareness across sessions
3. **Multi-Accountability Styles**: Tactical, Grace, or Analyst - user chooses
4. **Depth-Based Tone Adaptation**: Dynamic based on conversation depth
5. **Proactive Check-ins**: Scheduled via pg_cron, multi-channel
6. **CBT Integration**: Psychology Expert with therapeutic techniques
7. **Gritty, Realistic Support**: Not toxic positive, but disciplined

---

## Next Steps

1. **Set up pgvector extension** in PostgreSQL
2. **Design semantic memory schema** with pgvector
3. **Build Persona Router** with mode/style/state awareness
4. **Implement semantic memory extraction** from conversations
5. **Create accountability style wrappers** (Tactical, Grace, Analyst)
6. **Set up pg_cron** for scheduled check-ins
7. **Build Psychology Expert CBT system** with safety layers
8. **Integrate Twilio/WhatsApp** for notifications

---

**Prepared by**: SuperNinja  
**Based on**: User vision and requirements  
**Date**: 2025-01-17  
**Version**: 2.0