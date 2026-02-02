#!/usr/bin/env python3
"""
Test script to simulate discovery mode request without authentication
"""

import asyncio
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_discovery_mode_no_auth():
    """Test discovery mode without authentication"""
    print("Testing discovery mode without authentication...")
    
    response = client.post(
        "/api/v1/chat/message",
        json={
            "message": "Hello, I'm interested in learning more",
            "mode": "discovery",
            "conversation_id": None
        },
        headers={
            "Content-Type": "application/json"
            # No Authorization header
        }
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("✅ SUCCESS: Discovery mode works without authentication!")
        return True
    else:
        print("❌ FAILED: Discovery mode returned error")
        print(f"Error details: {response.json()}")
        return False

if __name__ == "__main__":
    success = test_discovery_mode_no_auth()
    sys.exit(0 if success else 1)