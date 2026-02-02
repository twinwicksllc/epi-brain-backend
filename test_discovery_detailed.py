#!/usr/bin/env python3
"""
Detailed test script to see the actual error message
"""

import asyncio
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_discovery_mode_detailed():
    """Test discovery mode and capture full error details"""
    print("=" * 80)
    print("Testing discovery mode with detailed error capture")
    print("=" * 80)
    
    response = client.post(
        "/api/v1/chat/message",
        json={
            "message": "Hello, I'm interested in learning more",
            "mode": "discovery",
            "conversation_id": None
        },
        headers={
            "Content-Type": "application/json"
        }
    )
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print(f"\nResponse Body:")
    print(json.dumps(response.json(), indent=2))
    
    return response.status_code == 200

if __name__ == "__main__":
    success = test_discovery_mode_detailed()
    sys.exit(0 if success else 1)