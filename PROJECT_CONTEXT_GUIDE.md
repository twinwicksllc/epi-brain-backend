# EPI Brain Backend - Project Context Guide

## Project Overview
This is the backend for a Personal Companion AI with accountability features. The project uses FastAPI with PostgreSQL for a proactive life partner AI.

## Key Features Implemented

### Phase 1: Enhanced Memory & Context System ✅
- Structured memory system with global and session memory
- Real-time information extraction from conversations
- Memory injection into AI prompts
- Natural, non-transactional data collection

### Phase 2: Accountability Infrastructure ✅ (Deployed)
- Core Variable Collection Service
- Active Memory Extraction Service
- Privacy Controls Service
- Memory Prompt Enhancer
- Response Parser for real-time variable extraction

### Current Status
- **Login**: ✅ Working
- **Chat**: ✅ Working
- **Phase 1 Memory**: ✅ Functional
- **Phase 2 Memory**: ✅ Re-implemented with safety improvements
- **User Name Memory**: ✅ Fixed - AI now remembers name across conversations
- **Timezone Collection**: ✅ Fixed - No longer asks repeatedly

## Repository Information
- **Repository**: `twinwicksllc/epi-brain-backend`
- **Branch**: `main`
- **GitHub CLI**: Use `gh` command for all GitHub operations
- **Deployment Platform**: Render

## Critical Files and Their Purposes

### Core Application Files
```
app/
├── main.py                    # FastAPI application entry point
├── config.py                  # Configuration settings including memory config
├── memory_config.py           # Memory system configuration (core, active, privacy variables)
└── database.py                # Database connection and session management
```

### API Endpoints
```
app/api/
├── auth.py                    # Authentication endpoints (login, register)
├── chat.py                    # Chat endpoints with Phase 2 memory integration
└── voice.py                   # Voice transcription endpoints
```

### Memory System Services (Phase 2)
```
app/services/
├── memory_service.py          # Core memory management (all methods async)
├── core_variable_collector.py # Guides AI in collecting core variables
├── active_memory_extractor.py # Auto-extracts info from conversations
├── privacy_controls.py        # Handles privacy-sensitive variables
├── memory_prompt_enhancer.py  # Integrates memory into AI prompts
└── response_parser.py         # Extracts core variables from user responses
```

### Database Models
```
app/models/
├── user.py                    # User model with global_memory and is_admin fields
└── conversation.py            # Conversation model with session_memory field
```

### Response Schemas
```
app/schemas/
├── user.py                    # UserResponse with global_memory and is_admin
└── conversation.py            # ConversationResponse with session_memory
```

### Recent Additions
```
├── DATABASE_MIGRATION_REQUIRED.md  # Guide for running database migrations
├── add_memory_columns.sql          # SQL migration script
└── migrate_database.py             # Python migration script
```

## Recent Issues and Fixes

### Issue 1: ModuleNotFoundError for memory_config
**Cause**: Created `config` directory when `app/config.py` was already a file  
**Fix**: Moved `memory_config.py` to `app/memory_config.py` and updated imports

### Issue 2: Database schema mismatch
**Cause**: New columns added to models but not in production database  
**Fix**: Created migration scripts, user ran them successfully

### Issue 3: Pydantic serialization errors
**Cause**: Response schemas didn't include new memory fields  
**Fix**: Added `session_memory: dict = {}` to `ConversationResponse` and `global_memory: dict = {}` and `is_admin: str = "false"` to `UserResponse`

### Issue 4: AI not remembering user's name
**Cause**: Async/sync mismatch in memory system  
**Fix**: Made all `MemoryService` methods async

### Issue 5: Name extraction extracting "in CST"
**Cause**: Patterns too generic  
**Fix**: Added more specific patterns and blacklist of invalid names

### Issue 6: AI asking for timezone repeatedly
**Cause**: Core variable collector appending questions to every response  
**Fix**: Modified to only ask occasionally with natural prompts

### Issue 7: 'logger' is not defined
**Cause**: `memory_service.py` using `logger` without importing it  
**Fix**: Added `import logging` and `logger = logging.getLogger(__name__)`

### Issue 8: 'coroutine' is not iterable
**Cause**: Internal method calls missing `await`  
**Fix**: Added `await` to all internal method calls in `MemoryService`

## Environment Variables Required
```bash
DATABASE_URL=postgresql://user:password@host:port/database
OPENAI_API_KEY=your_openai_api_key
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
MEMORY_ENABLED=true  # Set to false to disable Phase 2
```

## Database Schema

### Users Table
- id (primary key)
- email (unique)
- hashed_password
- global_memory (JSON) - stores global variables like name, location, timezone
- is_admin (boolean) - admin flag
- created_at
- updated_at

### Conversations Table
- id (primary key)
- user_id (foreign key)
- title
- session_memory (JSON) - stores session-specific information
- created_at
- updated_at

### Messages Table
- id (primary key)
- conversation_id (foreign key)
- role (user/assistant)
- content
- created_at

## Memory System Architecture

### Global Memory (User-level)
Persists across all conversations:
- **Core Variables**: name, location, timezone
- **Active Variables**: goals, preferences, relationships, routines, important_dates, health_info
- **Privacy Variables**: Only stored with user consent

### Session Memory (Conversation-level)
Temporary context for single conversation:
- Topics discussed
- Current context
- Temporary preferences
- Active goals being worked on

### Memory Flow
1. User sends message
2. `ResponseParser` extracts core variables from response
3. `ActiveMemoryExtractor` analyzes conversation for additional info
4. `MemoryService` updates both global and session memory
5. `MemoryPromptEnhancer` injects relevant memory into AI prompt
6. AI responds with personalized context

## Testing Checklist
- [ ] Login works
- [ ] Chat functionality works
- [ ] AI remembers user's name across conversations
- [ ] AI doesn't repeatedly ask for timezone
- [ ] Memory variables are being extracted and stored
- [ ] Global memory persists across conversations
- [ ] Session memory works within a conversation
- [ ] No async/await errors
- [ ] No logger errors

## Next Steps (Phase 3: Goal Setting & Accountability)
1. Implement database schema for goals and check-ins
2. Implement basic goal CRUD operations
3. Implement personality router with 3 core modes
4. Write system instruction blocks for each mode

## GitHub Workflow
All GitHub operations use the `gh` CLI:
```bash
# View status
gh repo view

# Commit changes
git add .
git commit -m "description"
git push

# View deployment status on Render
# Check Render dashboard
```

## Deployment Notes
- Backend automatically redeploys on push to main branch
- Check Render dashboard for deployment logs
- If deployment fails, check recent changes and logs

## Quick Start for New Developer
1. Clone repository: `gh repo clone twinwicksllc/epi-brain-backend`
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables
4. Run database migrations if needed
5. Start server: `uvicorn app.main:app --reload`
6. Test endpoints at http://localhost:8000
7. Check API docs at http://localhost:8000/docs

## Important Notes
- All memory service methods are async - always use `await`
- When adding new memory variables, update `memory_config.py`
- Response schemas must include all database fields
- Use `try/except` blocks when integrating new features
- Test thoroughly before pushing to production
- Monitor Render deployment logs for errors