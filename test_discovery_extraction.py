"""
Test script for Discovery Mode extraction logic
"""

import re

# Test the regex patterns
NAME_EXTRACTION_REGEX = re.compile(
    r"(?:my name is|i am|i'm|i am called|call me|this is|name is|name's)\s+([A-Za-z][A-Za-z'\-]*(?:\s+[A-Za-z][A-Za-z'\-]*){0,2})",
    re.IGNORECASE
)

INTENT_EXTRACTION_REGEX = re.compile(
    r"(?:here (?:to|for|because)|i'm here (?:to|for|because)|i came (?:to|for|because)|i'm looking (?:to|for)|i want (?:to|help with)|i need (?:to|help with)|looking for help with|need help with|want help with|hoping to|want to talk about|talk about|reaching out (?:to|because|for)|i've come to|help me with|struggling with|dealing with|working on|interested in)\s+(.+?)(?:[.!?]|$)",
    re.IGNORECASE
)

# Test cases
test_messages = [
    # Name extraction tests
    ("Hi, my name is John", "John", None),
    ("I am Sarah", "Sarah", None),
    ("Call me Mike", "Mike", None),
    ("I'm Jennifer Smith", "Jennifer Smith", None),
    ("This is Dr. Alex Johnson", "Dr", None),  # Should capture "Dr" (first word)
    
    # Intent extraction tests
    ("I'm here to improve my mental health", None, "improve my mental health"),
    ("I need help with anxiety", None, "anxiety"),
    ("I want to lose weight", None, "lose weight"),
    ("I'm struggling with stress", None, "stress"),
    ("I'm working on building better habits", None, "building better habits"),
    ("I'm interested in learning sales techniques", None, "learning sales techniques"),
    
    # Combined tests
    ("Hi! My name is Alex and I'm here to work on my confidence", "Alex", "work on my confidence"),
    ("I'm Sarah. I need help with managing stress.", "Sarah", "managing stress"),
]

print("=" * 80)
print("DISCOVERY MODE EXTRACTION TEST")
print("=" * 80)

for i, (message, expected_name, expected_intent) in enumerate(test_messages, 1):
    print(f"\n[Test {i}] Message: '{message}'")
    
    # Extract name
    name_match = NAME_EXTRACTION_REGEX.search(message)
    extracted_name = name_match.group(1) if name_match else None
    
    # Extract intent
    intent_match = INTENT_EXTRACTION_REGEX.search(message)
    extracted_intent = intent_match.group(1).strip().rstrip(".!?") if intent_match else None
    
    # Check results
    name_ok = extracted_name == expected_name or (expected_name and extracted_name and expected_name in extracted_name)
    intent_ok = extracted_intent == expected_intent
    
    print(f"  Expected Name: {expected_name}")
    print(f"  Extracted Name: {extracted_name} {'✓' if name_ok else '✗'}")
    print(f"  Expected Intent: {expected_intent}")
    print(f"  Extracted Intent: {extracted_intent} {'✓' if intent_ok else '✗'}")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)

# Test the bridge message template
print("\n\nBRIDGE MESSAGE TEMPLATE TEST:")
print("-" * 80)

DISCOVERY_MODE_SIGNUP_BRIDGE_TEMPLATE = (
    "I've got some great ideas for how we can tackle {intent} together, {name}! "
    "To keep this conversation going and unlock my full voice and emotional intelligence capabilities, "
    "let's get your free account set up real quick."
)

test_name = "Sarah"
test_intent = "managing stress"
bridge_message = DISCOVERY_MODE_SIGNUP_BRIDGE_TEMPLATE.format(name=test_name, intent=test_intent)

print(f"\nName: {test_name}")
print(f"Intent: {test_intent}")
print(f"\nBridge Message:\n{bridge_message}")
print("-" * 80)
