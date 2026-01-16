#!/bin/bash

# EPI Brain Backend - New Chat Startup Script
# This script sets up the environment and provides context for a new chat session

echo "=========================================="
echo "EPI Brain Backend - New Chat Startup"
echo "=========================================="
echo ""

# Step 1: Display project context
echo "📋 Step 1: Reading Project Context..."
echo "=========================================="
if [ -f "PROJECT_CONTEXT_GUIDE.md" ]; then
    echo "✓ PROJECT_CONTEXT_GUIDE.md found"
    echo ""
    echo "Key Points:"
    grep -E "^#{1,2}" PROJECT_CONTEXT_GUIDE.md | head -20
    echo ""
    echo "For full context, read: cat PROJECT_CONTEXT_GUIDE.md"
else
    echo "✗ PROJECT_CONTEXT_GUIDE.md not found"
fi
echo ""

# Step 2: Check current state
echo "📊 Step 2: Checking Current State..."
echo "=========================================="
if [ -f "CURRENT_STATE_SUMMARY.md" ]; then
    echo "✓ CURRENT_STATE_SUMMARY.md found"
    echo ""
    echo "Current Status:"
    grep -E "^##" CURRENT_STATE_SUMMARY.md | head -15
    echo ""
    echo "For full status, read: cat CURRENT_STATE_SUMMARY.md"
else
    echo "✗ CURRENT_STATE_SUMMARY.md not found"
fi
echo ""

# Step 3: Check git status
echo "🔍 Step 3: Git Status..."
echo "=========================================="
git status 2>/dev/null || echo "Not a git repository or git not available"
echo ""

# Step 4: Show recent commits
echo "📝 Step 4: Recent Commits..."
echo "=========================================="
git log --oneline -5 2>/dev/null || echo "Git history not available"
echo ""

# Step 5: Check if backend is running
echo "🚀 Step 5: Backend Status..."
echo "=========================================="
if pgrep -f "uvicorn" > /dev/null; then
    echo "✓ Backend is running"
    echo ""
    echo "Process info:"
    ps aux | grep uvicorn | grep -v grep
else
    echo "✗ Backend is not running"
    echo ""
    echo "To start: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
fi
echo ""

# Step 6: Check database connection
echo "💾 Step 6: Database Connection..."
echo "=========================================="
python3 -c "from app.database import engine; print('✓ Database connected')" 2>/dev/null || echo "✗ Database connection failed"
echo ""

# Step 7: Check environment variables
echo "🔑 Step 7: Environment Variables..."
echo "=========================================="
echo "DATABASE_URL: ${DATABASE_URL:+✓ Set (hidden)}"
echo "OPENAI_API_KEY: ${OPENAI_API_KEY:+✓ Set (hidden)}"
echo "SECRET_KEY: ${SECRET_KEY:+✓ Set (hidden)}"
echo "MEMORY_ENABLED: ${MEMORY_ENABLED:-Not set}"
echo ""

# Step 8: List essential files
echo "📁 Step 8: Essential Files..."
echo "=========================================="
echo "Documentation:"
ls -lh PROJECT_CONTEXT_GUIDE.md QUICK_START_NEW_CHAT.md CURRENT_STATE_SUMMARY.md ESSENTIAL_FILES_CHECKLIST.md 2>/dev/null || echo "Some docs missing"
echo ""
echo "Core Application:"
ls -lh app/main.py app/config.py app/memory_config.py 2>/dev/null || echo "Some core files missing"
echo ""
echo "API Endpoints:"
ls -lh app/api/*.py 2>/dev/null || echo "API files missing"
echo ""
echo "Memory Services:"
ls -lh app/services/*.py 2>/dev/null || echo "Service files missing"
echo ""

# Step 9: Quick health check
echo "🏥 Step 9: Quick Health Check..."
echo "=========================================="
if command -v curl > /dev/null; then
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✓ Health endpoint responding"
    else
        echo "✗ Health endpoint not responding (backend may not be running)"
    fi
else
    echo "curl not available for health check"
fi
echo ""

# Step 10: Display next steps
echo "🎯 Step 10: Next Steps..."
echo "=========================================="
echo "1. Read the context files:"
echo "   cat PROJECT_CONTEXT_GUIDE.md"
echo "   cat CURRENT_STATE_SUMMARY.md"
echo ""
echo "2. Check the quick start guide:"
echo "   cat QUICK_START_NEW_CHAT.md"
echo ""
echo "3. Review essential files:"
echo "   cat ESSENTIAL_FILES_CHECKLIST.md"
echo ""
echo "4. Start backend if not running:"
echo "   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "5. Test the application:"
echo "   curl http://localhost:8000/docs"
echo ""
echo "6. Check GitHub status:"
echo "   gh repo view"
echo ""
echo "=========================================="
echo "Startup Complete! Ready for development."
echo "=========================================="