"""Test OpenAI API connectivity and key validity"""

import os
import asyncio
import httpx
from app.config import settings

async def test_openai_api():
    """Test if OpenAI API key is valid and working"""
    
    api_key = settings.OPENAI_API_KEY
    
    print("=" * 60)
    print("OpenAI API Key Test")
    print("=" * 60)
    
    # Check if API key exists
    if not api_key:
        print("❌ OPENAI_API_KEY is NOT configured")
        print("\nTo fix:")
        print("1. Go to https://platform.openai.com/api-keys")
        print("2. Create an API key")
        print("3. Add to Render: OPENAI_API_KEY=sk-...")
        return False
    
    print(f"✅ OPENAI_API_KEY is configured")
    print(f"   Length: {len(api_key)} characters")
    print(f"   Starts with: {api_key[:10]}...")
    
    # Check if key format is valid
    if not api_key.startswith("sk-"):
        print("❌ Invalid API key format (should start with 'sk-')")
        return False
    
    print("✅ API key format is valid")
    
    # Test the API with a simple TTS request
    print("\nTesting OpenAI TTS API...")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/audio/speech",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o-mini-tts",
                    "voice": "coral",
                    "input": "Hello, this is a test.",
                    "response_format": "mp3",
                },
            )
            
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                audio_size = len(response.content)
                print(f"✅ API call successful!")
                print(f"   Audio size: {audio_size} bytes")
                print(f"\n🎉 OpenAI TTS is working correctly!")
                return True
            
            elif response.status_code == 401:
                print("❌ 401 Unauthorized - Invalid API key")
                print("\nTo fix:")
                print("1. Verify your API key is correct")
                print("2. Check if key was revoked or expired")
                return False
            
            elif response.status_code == 429:
                print("❌ 429 Too Many Requests - Rate limit exceeded")
                print("\nThis could mean:")
                print("1. Free tier quota exceeded")
                print("2. Rate limit exceeded")
                print("3. Account needs to be upgraded to paid")
                print("\nTo fix:")
                print("1. Add credit to your OpenAI account ($5-10 minimum)")
                print("2. Check usage at: https://platform.openai.com/usage")
                return False
            
            else:
                error_text = response.text
                print(f"❌ Error: {response.status_code}")
                print(f"   Details: {error_text}")
                return False
                
    except httpx.TimeoutException:
        print("❌ Request timed out")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    asyncio.run(test_openai_api())