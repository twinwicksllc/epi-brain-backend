"""
Test all 9 personality modes with Groq API
"""

from groq import Groq
import sys
import os

# Get API key from environment variable
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    print("❌ Error: GROQ_API_KEY environment variable not set")
    print("Please set it with: export GROQ_API_KEY=your_key_here")
    sys.exit(1)

# System prompts for each mode
PROMPTS = {
    "personal_friend": "You are a warm, empathetic personal friend providing emotional support.",
    "sales_agent": "You are an expert sales trainer specializing in NEBP methodology.",
    "student_tutor": "You are a patient, knowledgeable tutor helping students learn.",
    "kids_learning": "You are a fun, engaging teacher for young children.",
    "christian_companion": "You are a faithful Christian companion providing spiritual guidance.",
    "customer_service": "You are a professional customer service trainer.",
    "psychology_expert": "You are an emotionally intelligent psychology expert.",
    "business_mentor": "You are an experienced business mentor.",
    "weight_loss_coach": "You are a motivational weight loss coach."
}

def test_mode(client, mode_name, system_prompt):
    """Test a single personality mode"""
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Hello! Can you help me?"}
            ],
            temperature=0.7,
            max_tokens=150
        )
        
        ai_response = response.choices[0].message.content
        tokens = response.usage.total_tokens
        
        return True, ai_response[:100] + "...", tokens
        
    except Exception as e:
        return False, str(e), 0

def main():
    print("Testing All 9 Personality Modes with Groq API")
    print("="*70)
    
    client = Groq(api_key=api_key)
    
    results = []
    
    for mode_name, system_prompt in PROMPTS.items():
        print(f"\nTesting: {mode_name.replace('_', ' ').title()}")
        
        success, response, tokens = test_mode(client, mode_name, system_prompt)
        
        if success:
            print(f"   SUCCESS - {tokens} tokens")
            print(f"   Response: {response}")
            results.append((mode_name, "PASS"))
        else:
            print(f"   FAILED - {response}")
            results.append((mode_name, "FAIL"))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for mode_name, status in results:
        print(f"{status} {mode_name.replace('_', ' ').title()}")
    
    passed = sum(1 for _, status in results if "PASS" in status)
    total = len(results)
    
    print(f"\nResults: {passed}/{total} modes working")
    
    if passed == total:
        print("\nALL MODES WORKING PERFECTLY!")
    else:
        print(f"\n{total - passed} mode(s) need attention")

if __name__ == "__main__":
    main()