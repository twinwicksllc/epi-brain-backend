# README: Starting a New Chat in EPI Brain Backend Project

## Overview

This project is a Personal Companion AI backend with accountability features. When starting a new chat session, you need to understand the current state, recent changes, and next steps.

## Quick Start (3 Minutes)

### Option 1: Automated Setup (Recommended)
```bash
./NEW_CHAT_STARTUP_SCRIPT.sh
```

This script will:
- Display project context
- Check current state
- Show recent commits
- Verify backend status
- Test database connection
- List essential files
- Show next steps

### Option 2: Manual Setup
```bash
# Step 1: Read context (2 minutes)
cat PROJECT_CONTEXT_GUIDE.md
cat CURRENT_STATE_SUMMARY.md

# Step 2: Check status (1 minute)
git status
git log --oneline -5
ps aux | grep uvicorn

# Step 3: Verify backend
curl http://localhost:8000/health
```

## Documentation Files

### Must-Read (In Order)
1. **PROJECT_CONTEXT_GUIDE.md** - Complete project documentation
2. **QUICK_START_NEW_CHAT.md** - Quick start commands and setup
3. **CURRENT_STATE_SUMMARY.md** - Current status and next steps
4. **ESSENTIAL_FILES_CHECKLIST.md** - File reference and debugging guide

### Reference Documents
- **DATABASE_MIGRATION_REQUIRED.md** - Migration guide (if needed)
- **add_memory_columns.sql** - SQL migration script
- **migrate_database.py** - Python migration script

## Current Project Status

### Completed Phases
- ✅ **Phase 1**: Enhanced Memory & Context System
- ✅ **Phase 2**: Accountability Infrastructure (Hybrid Memory System)

### Current Phase
- 🚧 **Phase 3**: Goal Setting & Accountability (Planning)

### What's Working
- User authentication (login/register)
- Chat functionality with Phase 2 memory
- AI remembers user's name across conversations
- Timezone collection without repetition
- Core variable extraction
- Active memory extraction
- Privacy controls

### What's Next
1. Design database schema for goals and check-ins
2. Implement goal CRUD operations
3. Implement personality router with 3 core modes
4. Write system instruction blocks for each mode

## Key Technical Details

### Memory System Architecture
- **Global Memory**: User-level (persists across conversations)
- **Session Memory**: Conversation-level (temporary context)
- **Core Variables**: name, location, timezone (actively collected)
- **Active Variables**: goals, preferences, relationships (auto-extracted)
- **Privacy Variables**: Only stored with user consent

### Critical Patterns
- **ALL memory service methods are async** - always use `await`
- **Update both models AND schemas** when adding fields
- **Use `try/except` blocks** when integrating new features
- **Test locally before pushing** to production

### Common Issues & Solutions
- **AI not remembering info**: Check async/await in memory_service.py
- **Database schema mismatch**: Run migration scripts
- **Pydantic errors**: Update response schemas with all fields
- **Deployment failures**: Check Render logs and recent commits

## Repository Information
- **Repository**: `twinwicksllc/epi-brain-backend`
- **Branch**: `main`
- **Platform**: Render (auto-deploys on push)
- **GitHub CLI**: Use `gh` command for all operations

## Essential Commands

### Git Operations
```bash
git status                    # Check status
git log --oneline -5          # Recent commits
git add .                     # Stage changes
git commit -m "message"       # Commit
git push                      # Push to main
```

### Backend Operations
```bash
# Start backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Check health
curl http://localhost:8000/health

# View API docs
curl http://localhost:8000/docs
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

## File Structure

```
/workspace/
├── README_FOR_NEW_CHATS.md          # This file
├── PROJECT_CONTEXT_GUIDE.md          # Complete project guide
├── QUICK_START_NEW_CHAT.md           # Quick start commands
├── CURRENT_STATE_SUMMARY.md          # Current status
├── ESSENTIAL_FILES_CHECKLIST.md      # File reference
├── NEW_CHAT_STARTUP_SCRIPT.sh        # Automated setup script
├── app/
│   ├── main.py                       # FastAPI entry
│   ├── config.py                     # Main config
│   ├── memory_config.py              # Memory config
│   ├── database.py                   # DB connection
│   ├── api/
│   │   ├── auth.py                   # Auth endpoints
│   │   ├── chat.py                   # Chat with Phase 2
│   │   └── voice.py                  # Voice endpoints
│   ├── services/
│   │   ├── memory_service.py         # Core memory (async)
│   │   ├── core_variable_collector.py
│   │   ├── active_memory_extractor.py
│   │   ├── privacy_controls.py
│   │   ├── memory_prompt_enhancer.py
│   │   └── response_parser.py
│   ├── models/
│   │   ├── user.py                   # User model
│   │   └── conversation.py           # Conversation model
│   └── schemas/
│       ├── user.py                   # User schemas
│       └── conversation.py           # Conversation schemas
```

## Getting Help

### Check These First
1. **PROJECT_CONTEXT_GUIDE.md** - For comprehensive project info
2. **ESSENTIAL_FILES_CHECKLIST.md** - For debugging and file reference
3. **CURRENT_STATE_SUMMARY.md** - For current status and next steps

### Common Questions

**Q: How do I start working on a feature?**
A: Read PROJECT_CONTEXT_GUIDE.md, check CURRENT_STATE_SUMMARY.md, review the relevant files in ESSENTIAL_FILES_CHECKLIST.md, then start coding.

**Q: The AI isn't remembering information. What do I do?**
A: Check that all memory_service.py methods are async and use `await`. Verify the response_parser.py extraction patterns.

**Q: Deployment failed. What should I check?**
A: Check recent commits, verify all imports work, test locally, then check Render logs for specific errors.

**Q: How do I add a new memory variable?**
A: Update memory_config.py, add extraction logic to response_parser.py (if core) or active_memory_extractor.py (if active), test, and commit.

**Q: What phase are we on?**
A: Phase 3 (Goal Setting & Accountability). Phase 1 and 2 are complete and deployed.

## Pre-Work Checklist

Before starting any work:
- [ ] Read PROJECT_CONTEXT_GUIDE.md
- [ ] Read CURRENT_STATE_SUMMARY.md
- [ ] Check git status
- [ ] Review recent commits
- [ ] Verify backend is running
- [ ] Understand the feature
- [ ] Know which files to modify
- [ ] Plan the changes

After completing work:
- [ ] Test locally
- [ ] Check for errors
- [ ] Update documentation
- [ ] Update schemas if needed
- [ ] Commit with descriptive message
- [ ] Push to main
- [ ] Monitor deployment
- [ ] Verify success

## Contact & Resources

- **Repository**: `twinwicksllc/epi-brain-backend`
- **Branch**: `main`
- **Platform**: Render
- **GitHub CLI**: `gh` command
- **API Docs**: http://localhost:8000/docs (local)

## Final Notes

- This project uses FastAPI with PostgreSQL
- All memory service methods are async - always use `await`
- Response schemas must include all database fields
- Test thoroughly before pushing to production
- Monitor Render deployment logs after every push
- Document your changes as you go
- Ask if you're unsure about anything

---

**Good luck with your work! 🚀**