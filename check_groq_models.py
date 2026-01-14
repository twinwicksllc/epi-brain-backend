"""
Check available Groq models
"""

from groq import Groq
import os

# Get API key from environment variable
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    print("❌ Error: GROQ_API_KEY environment variable not set")
    print("Please set it with: export GROQ_API_KEY=your_key_here")
    exit(1)

try:
    client = Groq(api_key=api_key)
    
    # Try to list models
    print("🔍 Checking available Groq models...\n")
    
    models = client.models.list()
    
    print("✅ Available models:")
    for model in models.data:
        print(f"   - {model.id}")
        
except Exception as e:
    print(f"Error: {e}")
    print("\nTrying common model names...")
    
    # Try common models
    common_models = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "llama3-70b-8192",
        "llama3-8b-8192",
        "mixtral-8x7b-32768",
        "gemma-7b-it"
    ]
    
    for model_name in common_models:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=10
            )
            print(f"✅ {model_name} - WORKS!")
        except Exception as e:
            if "model_decommissioned" in str(e):
                print(f"❌ {model_name} - Decommissioned")
            elif "model_not_found" in str(e):
                print(f"❌ {model_name} - Not found")
            else:
                print(f"⚠️  {model_name} - Error: {str(e)[:50]}")