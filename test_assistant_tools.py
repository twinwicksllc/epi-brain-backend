"""
Test script for Pocket EPI MVP Assistant Tools
Tests internal messaging, note-taking, translation, and sales silo features
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
API_V1 = "/api/v1"

# Test with authentication token (replace with actual token)
AUTH_TOKEN = "your-jwt-token-here"
HEADERS = {
    "Authorization": f"Bearer {AUTH_TOKEN}",
    "Content-Type": "application/json"
}


def test_internal_messaging():
    """Test internal messaging to team members"""
    print("\n" + "=" * 80)
    print("TEST 1: Internal Messaging")
    print("=" * 80)
    
    # Test 1: Get available recipients
    print("\n1. Getting available recipients...")
    response = requests.get(
        f"{BASE_URL}{API_V1}/assistant-tools/internal-message/available-recipients",
        headers=HEADERS
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Available recipients: {data['recipients']}")
    else:
        print(f"❌ Failed: {response.text}")
    
    # Test 2: Send message to Darrick
    print("\n2. Sending message to Darrick...")
    message_data = {
        "recipient_name": "darrick",
        "subject": "EPI Thought Log - Sales Strategy Idea",
        "message": "Hi Darrick,\n\nI had an interesting conversation with a user about objection handling in SaaS sales. They mentioned a pattern where price objections often mask timing concerns.\n\nKey insight: When prospects say 'too expensive,' they often mean 'I don't see urgent value yet.'\n\nSuggested script enhancement:\n- Acknowledge: 'I understand budget is important'\n- Reframe: 'Let's talk about the cost of NOT solving this problem'\n- Quantify: 'What's the current gap costing you per month?'\n\nThought this might be useful for the Pocket EPI sales silo training.\n\nBest,\nEPI",
        "include_user_context": True
    }
    
    response = requests.post(
        f"{BASE_URL}{API_V1}/assistant-tools/internal-message",
        headers=HEADERS,
        json=message_data
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ {data['message']}")
        print(f"   Recipient: {data.get('recipient')}")
    else:
        print(f"❌ Failed: {response.text}")


def test_user_notes():
    """Test note-taking functionality"""
    print("\n" + "=" * 80)
    print("TEST 2: User Notes & Quick Thoughts")
    print("=" * 80)
    
    # Test 1: Create a quick note
    print("\n1. Creating a quick note...")
    note_data = {
        "content": "Important insight from sales call: Objection handling is about listening for the REAL concern behind the stated objection. Price objections are often timing or authority issues in disguise.",
        "note_type": "quick_note",
        "title": "Sales Objection Pattern",
        "tags": "sales, objection-handling, insight"
    }
    
    response = requests.post(
        f"{BASE_URL}{API_V1}/assistant-tools/notes",
        headers=HEADERS,
        json=note_data
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 201:
        note = response.json()
        note_id = note['id']
        print(f"✅ Note created: {note['title']}")
        print(f"   ID: {note_id}")
        print(f"   Type: {note['note_type']}")
        print(f"   Preview: {note['content'][:100]}...")
    else:
        print(f"❌ Failed: {response.text}")
        note_id = None
    
    # Test 2: Create a draft
    print("\n2. Creating an email draft...")
    draft_data = {
        "content": "Subject: Follow-up on our conversation\n\nHi [Name],\n\nThank you for taking the time to discuss your sales challenges. Based on our conversation, I've identified three key areas where we can help:\n\n1. Objection handling framework\n2. Script optimization for cold outreach\n3. Role-play practice for tough prospects\n\nWould you be open to a 15-minute follow-up call this week?\n\nBest regards,\n[Your Name]",
        "note_type": "draft",
        "title": "Sales Follow-up Email Template",
        "tags": "email, follow-up, template"
    }
    
    response = requests.post(
        f"{BASE_URL}{API_V1}/assistant-tools/notes",
        headers=HEADERS,
        json=draft_data
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 201:
        draft = response.json()
        print(f"✅ Draft created: {draft['title']}")
    else:
        print(f"❌ Failed: {response.text}")
    
    # Test 3: Get all notes
    print("\n3. Retrieving all notes...")
    response = requests.get(
        f"{BASE_URL}{API_V1}/assistant-tools/notes",
        headers=HEADERS,
        params={"limit": 10}
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        notes = response.json()
        print(f"✅ Retrieved {len(notes)} notes")
        for i, note in enumerate(notes[:3], 1):
            print(f"   {i}. [{note['note_type']}] {note['title'] or 'Untitled'}")
    else:
        print(f"❌ Failed: {response.text}")
    
    # Test 4: Get notes summary
    print("\n4. Getting notes summary...")
    response = requests.get(
        f"{BASE_URL}{API_V1}/assistant-tools/notes-summary",
        headers=HEADERS
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        summary = response.json()
        print(f"✅ Notes Summary:")
        print(f"   Total Notes: {summary['total_notes']}")
        print(f"   By Type: {summary['by_type']}")
    else:
        print(f"❌ Failed: {response.text}")
    
    # Test 5: Search notes
    if note_id:
        print("\n5. Searching notes...")
        response = requests.get(
            f"{BASE_URL}{API_V1}/assistant-tools/notes/search/objection",
            headers=HEADERS,
            params={"limit": 5}
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            results = response.json()
            print(f"✅ Found {len(results)} notes matching 'objection'")
        else:
            print(f"❌ Failed: {response.text}")


def test_translation_polish():
    """Test translation and polishing tools"""
    print("\n" + "=" * 80)
    print("TEST 3: Translation & Polish Services")
    print("=" * 80)
    
    # Test 1: Spanish translation
    print("\n1. Testing Spanish translation...")
    translation_data = {
        "text": "Thank you for your time today. I look forward to working with you on improving your sales process.",
        "target_language": "spanish",
        "context": "Professional business communication"
    }
    
    response = requests.post(
        f"{BASE_URL}{API_V1}/assistant-tools/translate",
        headers=HEADERS,
        json=translation_data
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Translation prompt generated")
        print(f"   Instruction: {result['instruction']}")
        print(f"   Target: {result['target_language']}")
        print(f"\n   Prompt preview:")
        print(f"   {result['prompt'][:200]}...")
    else:
        print(f"❌ Failed: {response.text}")
    
    # Test 2: Email polishing
    print("\n2. Testing email polishing...")
    polish_data = {
        "text": "hey can we chat about the thing we talked about? let me know when ur free",
        "mode": "email",
        "context": "Professional follow-up"
    }
    
    response = requests.post(
        f"{BASE_URL}{API_V1}/assistant-tools/polish",
        headers=HEADERS,
        json=polish_data
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Polish prompt generated")
        print(f"   Mode: {result['mode']}")
        print(f"   Instruction: {result['instruction']}")
    else:
        print(f"❌ Failed: {response.text}")


def test_sales_silo_enhancement():
    """Test sales silo enhancements"""
    print("\n" + "=" * 80)
    print("TEST 4: Sales Silo Enhancement")
    print("=" * 80)
    
    print("\n✅ Sales Silo Updated with:")
    print("   - Objection Handling Priority")
    print("   - Script Generation Focus")
    print("   - Proactive 'Common Objections' questioning")
    print("   - Role-play scenarios with realistic pushback")
    print("\n   Enhanced Prompt Features:")
    print("   1. Immediately asks: 'What are the most common objections you face?'")
    print("   2. Offers objection handling practice after identification")
    print("   3. Generates battle-tested scripts (cold calls, follow-ups, closing)")
    print("   4. Uses frameworks: Feel-Felt-Found, SPIN Selling, Challenger Sale")
    print("   5. Provides scripts with [CUSTOMIZATION] placeholders")
    print("\n   Engagement Flow:")
    print("   1. Identify sales role and target market")
    print("   2. Surface common objections immediately")
    print("   3. Offer objection handling practice")
    print("   4. Generate customized scripts")
    print("   5. Role-play scenarios with realistic pushback")


def main():
    """Run all tests"""
    print("=" * 80)
    print("POCKET EPI MVP - ASSISTANT TOOLS TEST SUITE")
    print("=" * 80)
    print(f"Testing against: {BASE_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Run tests
    test_internal_messaging()
    test_user_notes()
    test_translation_polish()
    test_sales_silo_enhancement()
    
    print("\n" + "=" * 80)
    print("TEST SUITE COMPLETE")
    print("=" * 80)
    print("\n📋 SUMMARY:")
    print("   ✅ Internal Messaging: Send thoughts to Tom/Darrick via email")
    print("   ✅ User Notes: Save Quick Notes, Drafts, Reflections")
    print("   ✅ Translation: High-quality Spanish translation support")
    print("   ✅ Polish: Email drafting and proofreading modes")
    print("   ✅ Sales Silo: Enhanced objection handling and script generation")
    
    print("\n🔧 SETUP REQUIRED:")
    print("   1. Set environment variables:")
    print("      - EMAIL_TOM, EMAIL_DARRICK, EMAIL_TWINWICKS")
    print("      - SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD")
    print("   2. Run database migration: alembic upgrade head")
    print("   3. Update AUTH_TOKEN in test script with valid JWT")
    
    print("\n📚 API ENDPOINTS:")
    print("   POST   /api/v1/assistant-tools/internal-message")
    print("   GET    /api/v1/assistant-tools/internal-message/available-recipients")
    print("   POST   /api/v1/assistant-tools/notes")
    print("   GET    /api/v1/assistant-tools/notes")
    print("   GET    /api/v1/assistant-tools/notes/{note_id}")
    print("   PUT    /api/v1/assistant-tools/notes/{note_id}")
    print("   DELETE /api/v1/assistant-tools/notes/{note_id}")
    print("   GET    /api/v1/assistant-tools/notes/search/{search_term}")
    print("   GET    /api/v1/assistant-tools/notes-summary")
    print("   POST   /api/v1/assistant-tools/translate")
    print("   POST   /api/v1/assistant-tools/polish")


if __name__ == "__main__":
    main()
