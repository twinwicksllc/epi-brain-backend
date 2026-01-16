# Quick Start Guide for New Chat in EPI Brain Backend Project

## Step 1: Initial Setup Commands

Run these commands immediately to get up to speed:

```bash
# Navigate to project directory
cd /workspace

# Check current Git status
git status

# View recent commits
git log --oneline -10

# Check GitHub repository info
gh repo view
```

## Step 2: Read the Project Context

```bash
# Read the comprehensive project guide
cat PROJECT_CONTEXT_GUIDE.md
```

## Step 3: Verify Current State

```bash
# Check if backend is running
ps aux | grep uvicorn

# Check recent logs
tail -50 logs/app.log 2>/dev/null || echo "No log file found"

# Verify database connection
python -c "from app.database import engine; print('Database connected:', engine)"
```

## Step 4: Review Critical Files

```bash
# List main application files
ls -la app/

# View configuration
cat app/config.py

# View memory configuration
cat app/memory_config.py

# Check recent changes
git diff HEAD~5
```

## Step 5: Test the Application

```bash
# Start the backend server (if not running)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or check if it's already running
curl http://localhost:8000/docs

# Test health endpoint
curl http://localhost:8000/health
```

## Step 6: Check Deployment Status

```bash
# View recent deployments (requires gh CLI)
gh deployments list --limit 5

# Or check Render dashboard directly
# Visit: https://dashboard.render.com/
```

## Step 7: Review Recent Issues

Check these files for recent issues and fixes:
- `DATABASE_MIGRATION_REQUIRED.md` - Database migration guide
- `migrate_database.py` - Migration script
- `add_memory_columns.sql` - SQL migration

## Essential Context for Development

### Memory System Status
- ✅ Phase 1: Basic memory working
- ✅ Phase 2: Hybrid memory system deployed and working
- 🔄 Phase 3: Goal setting & accountability (next)

### Key Technical Decisions
1. All memory service methods are async
2. Memory variables defined in `memory_config.py`
3. Response schemas must include all DB fields
4. Use `try/except` for new feature integration

### Common Gotchas
- Always use `await` with memory service methods
- Update both models AND schemas when adding fields
- Check Render logs after every push
- Test locally before pushing to main

### File Structure Reference
```
app/
├── main.py                    # FastAPI app entry
├── config.py                  # Main config
├── memory_config.py           # Memory variables config
├── database.py                # DB connection
├── api/
│   ├── auth.py                # Auth endpoints
│   ├── chat.py                # Chat with Phase 2
│   └── voice.py               # Voice endpoints
├── services/
│   ├── memory_service.py      # Core memory (async)
│   ├── core_variable_collector.py
│   ├── active_memory_extractor.py
│   ├── privacy_controls.py
│   ├── memory_prompt_enhancer.py
│   └── response_parser.py
├── models/
│   ├── user.py                # User model
│   └── conversation.py        # Conversation model
└── schemas/
    ├── user.py                # User schemas
    └── conversation.py        # Conversation schemas
```

## Quick Reference Commands

### Database Operations
```bash
# Run migration
python migrate_database.py

# Check database schema
python -c "from app.models import user, conversation; print('Models loaded')"
```

### Git Operations
```bash
# Commit changes
git add .
git commit -m "description"
git push

# View changes
git diff
git log --oneline -5
```

### Testing
```bash
# Test login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password"}'

# Test chat
curl -X POST http://localhost:8000/api/chat/message \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"conversation_id": 1, "content": "Hello"}'
```

### Debugging
```bash
# View logs
tail -f logs/app.log

# Check environment variables
env | grep -E "DATABASE|OPENAI|SECRET"

# Test database connection
python -c "from app.database import SessionLocal; db = SessionLocal(); print('DB OK')"
```

## Current Work Focus

**Next Phase (Phase 3): Goal Setting & Accountability**
1. Database schema for goals and check-ins
2. Basic goal CRUD operations
3. Personality router with 3 modes
4. System instruction blocks for each mode

## Questions to Ask When Starting New Chat

1. What phase are we working on? (Current: Phase 3 planning)
2. Are there any active bugs or issues?
3. What's the current deployment status?
4. Any recent changes I should be aware of?
5. What's the priority task for today?

## Safety Checks Before Making Changes

- [ ] Read `PROJECT_CONTEXT_GUIDE.md`
- [ ] Check current git status
- [ ] Review recent commits
- [ ] Test locally if possible
- [ ] Update schemas when updating models
- [ ] Use async/await correctly with memory services
- [ ] Add error handling with try/except
- [ ] Test after making changes
- [ ] Commit with descriptive message
- [ ] Monitor Render deployment

## Contact & Support

- Repository: `twinwicksllc/epi-brain-backend`
- Branch: `main`
- Deployment: Render
- GitHub CLI: Use `gh` for all operations