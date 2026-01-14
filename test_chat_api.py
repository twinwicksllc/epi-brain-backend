#!/usr/bin/env python3
"""
Test script to verify chat API is saving messages to database
"""
import requests
import json

# Backend URL
BACKEND_URL = "http://localhost:8000"

# First, login to get token
print("=== Testing Login ===")
login_response = requests.post(
    f"{BACKEND_URL}/api/v1/auth/login",
    json={
        "email": "twinwicksllc@gmail.com",
        "password": "Test12345678"
    }
)

if login_response.status_code == 200:
    token_data = login_response.json()
    access_token = token_data["access_token"]
    print(f"✅ Login successful!")
    print(f"   Access token: {access_token[:50]}...")
else:
    print(f"❌ Login failed: {login_response.status_code}")
    print(f"   Response: {login_response.text}")
    exit(1)

# Send a test message
print("\n=== Sending Test Message ===")
headers = {"Authorization": f"Bearer {access_token}"}

message_response = requests.post(
    f"{BACKEND_URL}/api/v1/chat/message",
    headers=headers,
    json={
        "message": "This is a test message for depth tracking",
        "mode": "personal_friend"
    }
)

if message_response.status_code == 200:
    response_data = message_response.json()
    print(f"✅ Message sent successfully!")
    print(f"   Conversation ID: {response_data.get('conversation_id')}")
    print(f"   Message ID: {response_data.get('message_id')}")
    print(f"   Content: {response_data.get('content', '')[:100]}...")
    print(f"   Depth: {response_data.get('depth')}")
else:
    print(f"❌ Message failed: {message_response.status_code}")
    print(f"   Response: {message_response.text}")
    exit(1)

# Check database
print("\n=== Checking Database ===")
import sqlite3
conn = sqlite3.connect('epi_brain.db')
cursor = conn.cursor()

# Check conversations
cursor.execute('SELECT COUNT(*) FROM conversations')
conv_count = cursor.fetchone()[0]
print(f"Conversations in database: {conv_count}")

if conv_count > 0:
    cursor.execute('SELECT id, mode, depth, depth_enabled FROM conversations ORDER BY created_at DESC LIMIT 1')
    conv = cursor.fetchone()
    print(f"Latest conversation:")
    print(f"  ID: {conv[0]}")
    print(f"  Mode: {conv[1]}")
    print(f"  Depth: {conv[2]}")
    print(f"  Depth Enabled: {conv[3]}")

# Check messages
cursor.execute('SELECT COUNT(*) FROM messages')
msg_count = cursor.fetchone()[0]
print(f"Messages in database: {msg_count}")

if msg_count > 0:
    cursor.execute('SELECT id, role, content, depth_score FROM messages ORDER BY created_at DESC LIMIT 1')
    msg = cursor.fetchone()
    print(f"Latest message:")
    print(f"  ID: {msg[0]}")
    print(f"  Role: {msg[1]}")
    print(f"  Content: {msg[2][:50]}...")
    print(f"  Depth Score: {msg[3]}")

conn.close()

print("\n=== Test Complete ===")