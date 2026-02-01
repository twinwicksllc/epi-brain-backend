"""
Discovery Mode Refinement - Test Suite and Examples
Tests the LLM-first approach, contextual validation, and refined strike logic.
"""

import asyncio
import json
from app.services.discovery_extraction_service import DiscoveryExtractionService


async def test_name_validation():
    """Test LLM-first name validation with contextual responses."""
    print("\n" + "="*80)
    print("TEST 1: LLM-FIRST NAME VALIDATION")
    print("="*80)
    
    service = DiscoveryExtractionService()
    
    test_cases = [
        {
            "input": "My name is Sarah",
            "description": "Simple name",
            "expected": {"is_name": True, "confidence": "high"}
        },
        {
            "input": "Skinna marinka dinka dink",
            "description": "Song/nonsense - should trigger contextual response",
            "expected": {"is_name": False, "input_type": "playful_nonsense"}
        },
        {
            "input": "I'm Alex and I'm struggling with anxiety",
            "description": "Name + intent mixed",
            "expected": {"is_name": True, "name_value": "Alex"}
        },
        {
            "input": "Hey there, just checking things out",
            "description": "Greeting, not a name",
            "expected": {"is_name": False, "input_type": "greeting"}
        },
        {
            "input": "Call me Jordan",
            "description": "Casual name introduction",
            "expected": {"is_name": True}
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n[Test {i}] {test['description']}")
        print(f"Input: \"{test['input']}\"")
        
        try:
            result = await service.validate_and_extract_name(test["input"])
            
            print(f"Result:")
            print(f"  - is_name: {result['is_name']}")
            print(f"  - input_type: {result['input_type']}")
            if result['name_value']:
                print(f"  - extracted_name: {result['name_value']}")
            print(f"  - confidence: {result['confidence']:.1f}")
            print(f"  - response: {result['contextual_response']}")
        except Exception as e:
            print(f"Error: {e}")


async def test_intent_validation():
    """Test LLM-first intent validation."""
    print("\n" + "="*80)
    print("TEST 2: LLM-FIRST INTENT VALIDATION")
    print("="*80)
    
    service = DiscoveryExtractionService()
    
    test_cases = [
        {
            "input": "I need help managing my anxiety",
            "name": "Sarah",
            "description": "Clear intent statement",
            "expected": {"is_intent": True}
        },
        {
            "input": "I don't know, maybe?",
            "name": "Jordan",
            "description": "Vague/dismissive response",
            "expected": {"is_intent": False}
        },
        {
            "input": "I'm struggling with work-life balance and want to build better habits",
            "name": "Alex",
            "description": "Detailed intent",
            "expected": {"is_intent": True, "intent_category": "productivity"}
        },
        {
            "input": "lol whatever",
            "name": "Jordan",
            "description": "Non-engagement",
            "expected": {"is_intent": False}
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n[Test {i}] {test['description']}")
        print(f"Name: {test['name']}")
        print(f"Input: \"{test['input']}\"")
        
        try:
            result = await service.validate_and_extract_intent(
                test["input"],
                captured_name=test["name"]
            )
            
            print(f"Result:")
            print(f"  - is_intent: {result['is_intent']}")
            if result['intent_value']:
                print(f"  - extracted_intent: {result['intent_value']}")
            print(f"  - intent_category: {result['intent_category']}")
            print(f"  - confidence: {result['confidence']:.1f}")
        except Exception as e:
            print(f"Error: {e}")


async def test_engagement_assessment():
    """Test engagement quality assessment (honest vs. not trying)."""
    print("\n" + "="*80)
    print("TEST 3: ENGAGEMENT QUALITY ASSESSMENT")
    print("="*80)
    
    service = DiscoveryExtractionService()
    
    test_cases = [
        {
            "input": "Skinna marinka dinka dink",
            "turn": 1,
            "description": "Playful nonsense on turn 1",
            "expected": {"engagement_pattern": "playful", "strike_weight": 1}
        },
        {
            "input": "I'm Alex",
            "turn": 1,
            "description": "Genuine attempt",
            "expected": {"engagement_pattern": "genuine", "is_engaged": True}
        },
        {
            "input": "whatever",
            "turn": 3,
            "description": "Dismissive on turn 3",
            "expected": {"engagement_pattern": "dismissive", "strike_weight": 2}
        },
        {
            "input": "fsdlfkdsflksdflk spam spam",
            "turn": 2,
            "description": "Clear spam/random",
            "expected": {"engagement_pattern": "clearly_not_trying", "strike_weight": 3}
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n[Test {i}] {test['description']}")
        print(f"Turn: {test['turn']}")
        print(f"Input: \"{test['input']}\"")
        
        try:
            result = await service.assess_engagement_quality(
                test["input"],
                conversation_turn=test["turn"]
            )
            
            print(f"Result:")
            print(f"  - engagement_pattern: {result['engagement_pattern']}")
            print(f"  - is_engaged: {result['is_engaged']}")
            print(f"  - is_honest_attempt: {result['is_honest_attempt']}")
            print(f"  - is_non_engagement: {result['is_non_engagement']}")
            print(f"  - strike_weight: {result['strike_weight']}")
            print(f"  - recommendation: {result['recommendation']}")
        except Exception as e:
            print(f"Error: {e}")


async def test_correction_detection():
    """Test correction detection (name clarification flow)."""
    print("\n" + "="*80)
    print("TEST 4: CORRECTION DETECTION")
    print("="*80)
    
    service = DiscoveryExtractionService()
    
    print("\nScenario: User initially said 'Alex' but it was wrong")
    print("Now they're providing the correction: 'No, I'm Alexandria'")
    
    try:
        result = await service.validate_and_extract_name(
            "No, I'm Alexandria",
            previous_name="Alex"
        )
        
        print(f"\nResult:")
        print(f"  - is_name: {result['is_name']}")
        print(f"  - is_correction: {result['is_correction']}")
        print(f"  - extracted_name: {result['name_value']}")
        print(f"  - recommendation: {result['contextual_response']}")
        
    except Exception as e:
        print(f"Error: {e}")


async def main():
    """Run all tests."""
    print("\n" + "🧪 "*40)
    print("DISCOVERY MODE REFINEMENT - TEST SUITE")
    print("🧪 "*40)
    
    try:
        await test_name_validation()
        await test_intent_validation()
        await test_engagement_assessment()
        await test_correction_detection()
        
        print("\n" + "="*80)
        print("ALL TESTS COMPLETED")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Test suite error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
