"""
Quick test script to verify Groq API integration
"""

from groq import Groq
import os

# Test Groq API
def test_groq_api():
    print("🧪 Testing Groq API Integration...\n")
    
    # Get API key from environment variable
    api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key:
        print("❌ Error: GROQ_API_KEY environment variable not set")
        print("Please set it with: export GROQ_API_KEY=your_key_here")
        return False
    
    try:
        # Initialize client
        client = Groq(api_key=api_key)
        print("✅ Groq client initialized successfully")
        
        # Test API call
        print("\n📤 Sending test message to Groq API...")
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a warm, empathetic personal friend providing emotional support."
                },
                {
                    "role": "user",
                    "content": "Hello! How are you today?"
                }
            ],
            temperature=0.7,
            max_tokens=1024
        )
        
        # Extract response
        ai_message = response.choices[0].message.content
        tokens_used = response.usage.total_tokens
        
        print("\n✅ API call successful!")
        print(f"\n📊 Response Details:")
        print(f"   - Model: {response.model}")
        print(f"   - Tokens used: {tokens_used}")
        print(f"   - Input tokens: {response.usage.prompt_tokens}")
        print(f"   - Output tokens: {response.usage.completion_tokens}")
        
        print(f"\n💬 AI Response:")
        print(f"   {ai_message}")
        
        print("\n" + "="*60)
        print("🎉 SUCCESS! Groq API is working perfectly!")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    test_groq_api()