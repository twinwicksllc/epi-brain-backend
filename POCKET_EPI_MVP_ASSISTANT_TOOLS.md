# Pocket EPI MVP - Assistant Tools Quick Reference

**Commit**: `b6017df` - Successfully deployed to GitHub

---

## 🚀 Features Implemented

### 1. **Flexible Internal Messaging**
Send thoughts or notes to specific team members by name.

**Endpoints:**
- `POST /api/v1/assistant-tools/internal-message` - Send message
- `GET /api/v1/assistant-tools/internal-message/available-recipients` - List recipients

**Usage Example:**
```bash
curl -X POST http://localhost:8000/api/v1/assistant-tools/internal-message \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "recipient_name": "darrick",
    "subject": "Sales Insight from User Conversation",
    "message": "Key pattern identified: Price objections often mask timing concerns.",
    "include_user_context": true
  }'
```

**Team Members Mapped:**
- `tom` → `EMAIL_TOM`
- `darrick` → `EMAIL_DARRICK`
- `twinwicks` → `EMAIL_TWINWICKS`

---

### 2. **Thought Log & Quick Notes**
Save Quick Notes, Drafts, Reflections, and Thoughts directly to the database.

**Endpoints:**
- `POST /api/v1/assistant-tools/notes` - Create note
- `GET /api/v1/assistant-tools/notes` - List notes (with filters)
- `GET /api/v1/assistant-tools/notes/{note_id}` - Get specific note
- `PUT /api/v1/assistant-tools/notes/{note_id}` - Update note
- `DELETE /api/v1/assistant-tools/notes/{note_id}` - Delete note
- `GET /api/v1/assistant-tools/notes/search/{term}` - Search notes
- `GET /api/v1/assistant-tools/notes-summary` - Get statistics

**Note Types:**
- `quick_note` - Fast thoughts and insights
- `draft` - Email drafts, messages, content
- `reflection` - Deep thinking, analysis
- `thought` - Ideas, brainstorms

**Usage Example:**
```bash
curl -X POST http://localhost:8000/api/v1/assistant-tools/notes \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Insight: Sales objections reveal deeper concerns",
    "note_type": "quick_note",
    "title": "Objection Handling Pattern",
    "tags": "sales, insight, objection-handling"
  }'
```

**Database Schema:**
- Links to conversations (`conversation_id`)
- Tracks personality mode (`personality_mode`)
- Supports tagging (`tags`)
- Timestamps (`created_at`, `updated_at`)

---

### 3. **Translation & Polish Service**
High-quality Spanish translation and email drafting/proofreading.

**Endpoints:**
- `POST /api/v1/assistant-tools/translate` - Translation
- `POST /api/v1/assistant-tools/polish` - Proofreading

**Translation Example:**
```bash
curl -X POST http://localhost:8000/api/v1/assistant-tools/translate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Thank you for your time today.",
    "target_language": "spanish",
    "context": "Professional business communication"
  }'
```

**Polish Modes:**
- `email` - Professional email format
- `formal` - Formal business communication
- `casual` - Friendly, approachable tone
- `professional` - Polished professional writing

**Polish Example:**
```bash
curl -X POST http://localhost:8000/api/v1/assistant-tools/polish \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "hey can we chat about that thing?",
    "mode": "email",
    "context": "Follow-up message"
  }'
```

---

### 4. **Sales Silo Enhancement**
Enhanced sales discovery mode with objection handling priority.

**Key Features:**
- Proactively asks: "What are the most common objections you face?"
- Offers immediate role-play practice for identified objections
- Generates battle-tested scripts (cold calls, follow-ups, closing)
- Uses proven frameworks: Feel-Felt-Found, SPIN Selling, Challenger Sale
- Scripts include [CUSTOMIZATION] placeholders

**Engagement Flow:**
1. Identify sales role and target market
2. Surface common objections immediately
3. Offer objection handling practice
4. Generate customized scripts
5. Role-play scenarios with realistic pushback

**Script Types Generated:**
- Cold call openers
- Objection responses (price, timing, competition, authority)
- Follow-up sequences
- Closing techniques

---

## 🔧 Setup & Configuration

### Environment Variables Required

```bash
# Team Email Addresses
EMAIL_TOM=tom@example.com
EMAIL_DARRICK=darrick@example.com
EMAIL_TWINWICKS=twinwicks@example.com

# SMTP Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@example.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=epi-assistant@example.com
SMTP_FROM_NAME=EPI Assistant
```

### Database Migration

```bash
# Run migration to create user_notes table
alembic upgrade head
```

**Migration Details:**
- Creates `user_notes` table
- Adds 6 indexes for optimized queries
- Composite indexes: `user_id + note_type`, `user_id + created_at`

---

## 📊 Use Cases

### For Darrick (Thinking Partner)
```
EPI: "I've been thinking about your sales strategy. Here's what I noticed..."
→ Saves insight as quick_note
→ Messages Darrick via internal messaging
→ Available for future reference
```

### For Tom (Technical Insights)
```
User reports bug pattern → EPI creates note → Messages Tom
EPI tracks patterns across conversations → Identifies trends
```

### For Sales Training
```
User: "I'm struggling with price objections"
EPI: "What are your most common objections?"
→ Generates objection handling scripts
→ Role-plays scenarios
→ Saves winning responses as notes
```

### For Spanish Communication
```
User needs Spanish email
→ POST /assistant-tools/translate
→ High-quality professional translation
→ Saves as draft note for future use
```

---

## 🧪 Testing

Run comprehensive test suite:
```bash
python test_assistant_tools.py
```

**Test Coverage:**
- Internal messaging (2 tests)
- Note CRUD operations (5 tests)
- Search and summary (2 tests)
- Translation and polish (2 tests)
- Sales silo verification (1 test)

---

## 📈 Next Steps

1. **Integration**: Wire up translation/polish to actual LLM service
2. **AI Tools**: Connect notes and messaging to chat API for automatic capture
3. **Analytics**: Track most-used note types and message patterns
4. **Mobile**: Optimize note-taking for mobile voice capture
5. **Export**: Add note export (PDF, Markdown) functionality

---

## 🎯 Success Metrics

**Goal**: Enable Darrick to use EPI as a true thinking partner

**Measurements:**
- Notes created per session
- Internal messages sent to team
- Translation/polish requests
- Sales silo objection practice sessions
- Note search frequency (indicates re-use)

---

## 🔒 Security

- All endpoints require JWT authentication
- Notes isolated by `user_id` (authorization checks)
- Internal messaging limited to configured team members
- SMTP credentials from environment variables (not hardcoded)

---

## 📝 API Documentation

Full OpenAPI documentation available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

**Tag**: "Assistant Tools" - All 11 endpoints grouped together

---

**Status**: ✅ Deployed and ready for use
**Version**: Pocket EPI MVP - February 3, 2026
**Commit**: `b6017df`
