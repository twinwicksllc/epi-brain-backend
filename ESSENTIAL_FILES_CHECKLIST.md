# Essential Files Checklist for New Chat

## Must-Read Files (Read in Order)

### 1. Project Overview
- [ ] `PROJECT_CONTEXT_GUIDE.md` - Complete project documentation
- [ ] `QUICK_START_NEW_CHAT.md` - Quick start commands and setup
- [ ] `CURRENT_STATE_SUMMARY.md` - Current status and next steps

### 2. Database & Migration
- [ ] `DATABASE_MIGRATION_REQUIRED.md` - Migration guide (if needed)
- [ ] `add_memory_columns.sql` - SQL migration script
- [ ] `migrate_database.py` - Python migration script

## Core Application Files (Review as Needed)

### Configuration
- [ ] `app/config.py` - Main application configuration
- [ ] `app/memory_config.py` - Memory system configuration

### Database
- [ ] `app/database.py` - Database connection management
- [ ] `app/models/user.py` - User model with memory fields
- [ ] `app/models/conversation.py` - Conversation model with memory fields

### API Endpoints
- [ ] `app/api/auth.py` - Authentication (login, register)
- [ ] `app/api/chat.py` - Chat with Phase 2 memory integration
- [ ] `app/api/voice.py` - Voice transcription

### Memory Services (Phase 2)
- [ ] `app/services/memory_service.py` - Core memory management (ALL METHODS ASYNC)
- [ ] `app/services/core_variable_collector.py` - Core variable collection
- [ ] `app/services/active_memory_extractor.py` - Auto-extraction from conversations
- [ ] `app/services/privacy_controls.py` - Privacy management
- [ ] `app/services/memory_prompt_enhancer.py` - Memory injection into prompts
- [ ] `app/services/response_parser.py` - Real-time variable extraction

### Response Schemas
- [ ] `app/schemas/user.py` - User response schemas (includes memory fields)
- [ ] `app/schemas/conversation.py` - Conversation response schemas (includes memory fields)

### Main Application
- [ ] `app/main.py` - FastAPI application entry point

## Quick Reference for Common Tasks

### Starting a New Chat Session

**Step 1: Read Context (5 minutes)**
```bash
cat PROJECT_CONTEXT_GUIDE.md
cat QUICK_START_NEW_CHAT.md
cat CURRENT_STATE_SUMMARY.md
```

**Step 2: Check Status (2 minutes)**
```bash
git status
git log --oneline -5
gh repo view
ps aux | grep uvicorn
```

**Step 3: Verify Backend (2 minutes)**
```bash
curl http://localhost:8000/health
curl http://localhost:8000/docs
```

**Step 4: Review Recent Changes (5 minutes)**
```bash
git diff HEAD~5
# Or review specific files based on task
```

### Debugging Common Issues

#### AI Not Remembering Information
```bash
# Check memory service
cat app/services/memory_service.py
# Verify all methods are async
# Check for missing await keywords

# Check response parser
cat app/services/response_parser.py
# Verify extraction patterns
```

#### Database Schema Issues
```bash
# Check models
cat app/models/user.py
cat app/models/conversation.py

# Check schemas
cat app/schemas/user.py
cat app/schemas/conversation.py

# Verify fields match
```

#### Deployment Errors
```bash
# Check Render logs
gh deployments list --limit 5
# Visit Render dashboard

# Check recent commits
git log --oneline -10
```

#### Async/Await Errors
```bash
# Search for async issues
grep -r "await" app/services/
grep -r "async def" app/services/

# Verify memory service
cat app/services/memory_service.py
# ALL methods must be async
# ALL internal calls must use await
```

### Making Changes

#### Adding New Memory Variable
1. Update `app/memory_config.py`
2. Update `app/services/response_parser.py` (if core variable)
3. Update `app/services/active_memory_extractor.py` (if active variable)
4. Test extraction
5. Commit changes

#### Adding New API Endpoint
1. Create endpoint in appropriate `app/api/` file
2. Create/update schema in `app/schemas/`
3. Update `app/main.py` if needed
4. Test endpoint
5. Commit changes

#### Adding New Database Field
1. Update model in `app/models/`
2. Update schema in `app/schemas/`
3. Create migration script
4. Run migration
5. Test changes
6. Commit changes

## Critical Patterns to Remember

### Memory Service Usage
```python
# CORRECT - Always use await
memory = await memory_service.get_global_memory(user_id)

# INCORRECT - Will cause errors
memory = memory_service.get_global_memory(user_id)
```

### Database Queries with Relationships
```python
# CORRECT - Use direct queries
message_count = db.query(Message).filter(
    Message.conversation_id == conversation_id
).count()

# INCORRECT - Can fail in intermediate state
message_count = len(conversation.messages)
```

### Error Handling
```python
# CORRECT - Use try/except for new features
try:
    from app.services.memory_service import MemoryService
    memory_service = MemoryService()
    # Use memory_service
except ImportError:
    logger.warning("Memory service not available")
    # Fallback behavior
```

### Updating Schemas
```python
# CORRECT - Add ALL database fields to schema
class UserResponse(BaseModel):
    id: int
    email: str
    global_memory: dict = {}  # Don't forget this!
    is_admin: str = "false"   # Or this!

# INCORRECT - Missing fields
class UserResponse(BaseModel):
    id: int
    email: str
    # Missing global_memory and is_admin!
```

## File Search Commands

### Find All Files Related to Memory
```bash
find . -name "*memory*" -type f
grep -r "memory" app/ --include="*.py"
```

### Find All API Endpoints
```bash
grep -r "@router" app/api/
grep -r "def " app/api/ | grep -E "(get|post|put|delete)"
```

### Find All Database Models
```bash
ls -la app/models/
grep -r "class.*Base" app/models/
```

### Find All Schemas
```bash
ls -la app/schemas/
grep -r "class.*BaseModel" app/schemas/
```

## Testing Commands

### Test Authentication
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password"}'
```

### Test Chat with Memory
```bash
curl -X POST http://localhost:8000/api/chat/message \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"conversation_id": 1, "content": "What is my name?"}'
```

### Test Health
```bash
curl http://localhost:8000/health
```

### Test Memory Endpoints
```bash
# Get global memory
curl -X GET http://localhost:8000/api/memory/global \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get session memory
curl -X GET http://localhost:8000/api/memory/session/1 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Pre-Work Checklist

### Before Making Any Changes
- [ ] Read PROJECT_CONTEXT_GUIDE.md
- [ ] Read CURRENT_STATE_SUMMARY.md
- [ ] Check git status
- [ ] Review recent commits
- [ ] Verify backend is running
- [ ] Understand the feature being changed
- [ ] Know which files to modify
- [ ] Plan the changes

### After Making Changes
- [ ] Test locally
- [ ] Check for errors
- [ ] Verify functionality
- [ ] Update documentation
- [ ] Update schemas if needed
- [ ] Commit with descriptive message
- [ ] Push to main
- [ ] Monitor Render deployment
- [ ] Verify deployment success

## Phase-Specific Checklists

### Phase 2 (Memory System) - COMPLETED ✅
- [x] Core variable collection
- [x] Active memory extraction
- [x] Privacy controls
- [x] Memory prompt enhancement
- [x] Response parser
- [x] All async/await issues fixed
- [x] All logger issues fixed
- [x] Database schema updated
- [x] Response schemas updated
- [x] Deployment successful

### Phase 3 (Goal Setting & Accountability) - IN PROGRESS 🚧
- [ ] Database schema for goals
- [ ] Database schema for check-ins
- [ ] Goal CRUD operations
- [ ] Check-in system
- [ ] Personality router (3 modes)
- [ ] System instruction blocks
- [ ] Integration with memory system
- [ ] Testing
- [ ] Documentation
- [ ] Deployment

## Emergency Procedures

### If Backend Won't Start
```bash
# Check logs
tail -50 logs/app.log

# Check port conflicts
lsof -i :8000

# Check environment variables
env | grep -E "DATABASE|OPENAI|SECRET"

# Test database connection
python -c "from app.database import engine; print(engine)"
```

### If Deployment Fails
```bash
# Check recent changes
git diff HEAD~1

# Check syntax errors
python -m py_compile app/main.py

# Check imports
python -c "from app.main import app"

# Revert if needed
git revert HEAD
```

### If Memory System Fails
```bash
# Check memory service
python -c "from app.services.memory_service import MemoryService"

# Check async methods
grep -A 5 "async def" app/services/memory_service.py

# Temporarily disable
# Set MEMORY_ENABLED = False in app/config.py
```

## Quick File Locations

```
Memory System:
  Config: app/memory_config.py
  Service: app/services/memory_service.py
  Collector: app/services/core_variable_collector.py
  Extractor: app/services/active_memory_extractor.py
  Privacy: app/services/privacy_controls.py
  Enhancer: app/services/memory_prompt_enhancer.py
  Parser: app/services/response_parser.py

API:
  Auth: app/api/auth.py
  Chat: app/api/chat.py
  Voice: app/api/voice.py

Database:
  Connection: app/database.py
  User Model: app/models/user.py
  Conversation Model: app/models/conversation.py

Schemas:
  User: app/schemas/user.py
  Conversation: app/schemas/conversation.py

Config:
  Main: app/config.py
  Entry: app/main.py
```

## Final Notes

- Always read the context files first
- Check git status before starting
- Test locally before pushing
- Use `await` with memory services
- Update schemas when updating models
- Monitor Render deployment
- Document your changes
- Ask if unsure about anything