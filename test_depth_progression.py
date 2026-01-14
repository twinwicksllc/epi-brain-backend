#!/usr/bin/env python3
"""
Test script to send progressively deeper messages to see color evolution
"""
import requests
import time

# Backend URL
BACKEND_URL = "http://localhost:8000"

# Login
print("=== Logging in ===")
login_response = requests.post(
    f"{BACKEND_URL}/api/v1/auth/login",
    json={
        "email": "twinwicksllc@gmail.com",
        "password": "Test12345678"
    }
)

if login_response.status_code != 200:
    print(f"❌ Login failed: {login_response.status_code}")
    print(login_response.text)
    exit(1)

token_data = login_response.json()
access_token = token_data["access_token"]
print(f"✅ Logged in successfully")

headers = {"Authorization": f"Bearer {access_token}"}

# Progressively deeper messages
messages = [
    ("Hi, how are you?", "Surface level"),
    ("I've been thinking about my goals lately.", "Shallow"),
    ("I'm feeling really anxious about my career path and don't know what to do.", "Deep"),
    ("I've been struggling with finding meaning in my life. Sometimes I feel empty and wonder if I'm on the right path. How do you find purpose when everything feels meaningless?", "Profound")
]

conversation_id = None

print("\n=== Sending progressively deeper messages ===\n")

for i, (message, level) in enumerate(messages, 1):
    print(f"\n📝 Message {i} ({level}):")
    print(f'   "{message[:60]}..."')
    
    response = requests.post(
        f"{BACKEND_URL}/api/v1/chat/message",
        headers=headers,
        json={
            "message": message,
            "conversation_id": conversation_id,
            "mode": "personal_friend"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        conversation_id = data.get('conversation_id')
        depth = data.get('depth')
        
        # Convert depth to percentage
        depth_pct = int((depth or 0) * 100)
        
        print(f"   ✅ Sent successfully")
        print(f"   📊 Depth: {depth or 0:.2f} ({depth_pct}%)")
        
        if depth_pct < 25:
            color = "🟣 Light Purple"
        elif depth_pct < 50:
            color = "🟣 Medium-Light Purple"
        elif depth_pct < 75:
            color = "🟣 Medium-Dark Purple"
        else:
            color = "🟣🔥 Dark Purple (Profound)"
        
        print(f"   🎨 Background: {color}")
    else:
        print(f"   ❌ Failed: {response.status_code}")
        print(f"      {response.text}")
    
    time.sleep(1)  # Small delay between messages

print("\n=== Test Complete ===")
print(f"\n💡 Now refresh your browser and check the conversation!")
print(f"   The background should have darkened with each message.")