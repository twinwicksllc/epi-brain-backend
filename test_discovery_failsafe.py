"""
Test script for Discovery Mode Failsafe
"""

import re

# Test the engagement detection logic
NAME_EXTRACTION_REGEX = re.compile(
    r"(?:my name is|i am called|call me|this is|name is|name's)\s+([A-Za-z][A-Za-z'\-]*(?:\s+[A-Za-z][A-Za-z'\-]*){0,2})(?:\s|[.,!?]|$)",
    re.IGNORECASE
)

INTENT_EXTRACTION_REGEX = re.compile(
    r"(?:here (?:to|for|because)|i'm here (?:to|for|because)|i came (?:to|for|because)|i'm looking (?:to|for)|i want (?:to|help with)|i need (?:to|help with)|looking for help with|need help with|want help with|hoping to|want to talk about|talk about|reaching out (?:to|because|for)|i've come to|help me with|struggling with|dealing with|working on|interested in)\s+(.+?)(?:[.!?]|$)",
    re.IGNORECASE
)

def check_engagement(message: str) -> tuple:
    """Check if message contains name or intent."""
    name_match = NAME_EXTRACTION_REGEX.search(message)
    intent_match = INTENT_EXTRACTION_REGEX.search(message)
    
    has_name = bool(name_match)
    has_intent = bool(intent_match)
    engaged = has_name or has_intent
    
    return engaged, has_name, has_intent

# Test cases: (message, should_be_engaged, description)
test_cases = [
    # Engaged - Name provided
    ("My name is John", True, "Name provided"),
    ("Call me Sarah", True, "Name provided (call me)"),
    ("I'm Alex", True, "Name provided (I'm)"),
    
    # Engaged - Intent provided
    ("I need help with anxiety", True, "Intent provided"),
    ("I'm here to work on my confidence", True, "Intent provided (here to)"),
    ("I'm struggling with stress", True, "Intent provided (struggling)"),
    ("I want to lose weight", True, "Intent provided (want to)"),
    
    # Engaged - Both provided
    ("Hi, my name is Mike and I need help with sales", True, "Both name and intent"),
    
    # NOT Engaged - Off-topic/irrelevant
    ("What's the weather like?", False, "Off-topic question"),
    ("Tell me a joke", False, "Off-topic request"),
    ("How do I make lasagna?", False, "Recipe request"),
    ("Can you help me with my homework?", False, "Generic help request"),
    ("What time is it?", False, "Time question"),
    ("Hello", False, "Generic greeting"),
    ("Cool!", False, "Generic response"),
    ("I don't know", False, "Vague response"),
    ("Maybe later", False, "Evasive response"),
    
    # Edge cases
    ("I'm interested in learning more", True, "Intent (interested in)"),
    ("I'm working on building confidence", True, "Intent (working on)"),
    ("I want help with managing my time", True, "Intent (want help with)"),
]

print("=" * 80)
print("DISCOVERY FAILSAFE ENGAGEMENT TEST")
print("=" * 80)

passed = 0
failed = 0

for i, (message, expected_engaged, description) in enumerate(test_cases, 1):
    engaged, has_name, has_intent = check_engagement(message)
    
    result = "✓ PASS" if engaged == expected_engaged else "✗ FAIL"
    if engaged == expected_engaged:
        passed += 1
    else:
        failed += 1
    
    print(f"\n[Test {i}] {description}")
    print(f"  Message: '{message}'")
    print(f"  Expected: {'Engaged' if expected_engaged else 'Not Engaged'}")
    print(f"  Got: {'Engaged' if engaged else 'Not Engaged'}")
    print(f"  Details: Name={has_name}, Intent={has_intent}")
    print(f"  {result}")

print("\n" + "=" * 80)
print(f"TEST RESULTS: {passed} passed, {failed} failed out of {len(test_cases)} tests")
print("=" * 80)

# Simulate strike counter logic
print("\n\nSTRIKE COUNTER SIMULATION:")
print("-" * 80)

conversation_messages = [
    "Hello",  # Strike 1 (no engagement)
    "What's the weather?",  # Strike 2 (no engagement)
    "Tell me a joke",  # Strike 3 (no engagement) -> FAILSAFE TRIGGERED
    "My name is John",  # Would not be processed (failsafe active)
]

strike_count = 0
MAX_STRIKES = 3
failsafe_triggered = False

for i, msg in enumerate(conversation_messages, 1):
    print(f"\nMessage {i}: '{msg}'")
    
    if failsafe_triggered:
        print(f"  ⚠️  FAILSAFE ACTIVE - Message not processed by LLM")
        print(f"  Response: 'I'd love to help you with that! To unlock my full capabilities...'")
        continue
    
    engaged, has_name, has_intent = check_engagement(msg)
    
    if engaged:
        print(f"  ✓ User engaged (Name={has_name}, Intent={has_intent})")
        print(f"  Strike count reset to 0")
        strike_count = 0
    else:
        strike_count += 1
        print(f"  ✗ No engagement detected")
        print(f"  Strike count: {strike_count}/{MAX_STRIKES}")
        
        if strike_count >= MAX_STRIKES:
            failsafe_triggered = True
            print(f"  🚫 FAILSAFE TRIGGERED - Future messages will not use LLM")

print("\n" + "-" * 80)
print(f"Final state: Strike count = {strike_count}, Failsafe = {failsafe_triggered}")
print("-" * 80)
