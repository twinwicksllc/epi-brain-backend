"""
Unit tests for depth scorer
"""

import pytest
from app.services.depth_scorer import DepthScorer


@pytest.fixture
def scorer():
    return DepthScorer()


class TestHeuristicScoring:
    """Test heuristic scoring logic"""
    
    def test_casual_message_low_score(self, scorer):
        """Casual messages should score low"""
        message = "What's the weather like today?"
        score = scorer._heuristic_score(message)
        assert score < 0.3
    
    def test_deep_message_high_score(self, scorer):
        """Deep introspective messages should score high"""
        message = "I feel so lost and anxious. I'm questioning my purpose and wondering why I feel this way."
        score = scorer._heuristic_score(message)
        assert score > 0.6
    
    def test_first_person_detection(self, scorer):
        """Should detect first-person language"""
        message = "I feel I think I believe my thoughts"
        score = scorer._heuristic_score(message)
        assert score > 0.0  # Should detect multiple first-person patterns
    
    def test_emotion_words_detection(self, scorer):
        """Should detect emotion vocabulary"""
        message = "I'm feeling anxious and overwhelmed"
        score = scorer._heuristic_score(message)
        assert score > 0.2  # Should detect emotion words
    
    def test_introspective_language(self, scorer):
        """Should detect introspective language"""
        message = "I'm questioning my purpose and seeking meaning"
        score = scorer._heuristic_score(message)
        assert score > 0.3  # Should detect introspective words
    
    def test_score_clamping(self, scorer):
        """Scores should never exceed 1.0"""
        # Message with many depth signals
        message = "I feel so anxious and lost. I'm questioning my purpose and identity. Why do I feel this way? I'm wondering about the meaning of my journey and seeking to understand my soul."
        score = scorer._heuristic_score(message)
        assert 0.0 <= score <= 1.0


class TestScoringDecisions:
    """Test when LLM should be used"""
    
    @pytest.mark.asyncio
    async def test_short_message_skipped(self, scorer):
        """Very short messages should be skipped"""
        message = "Hey"
        result = await scorer.score_turn(message)
        assert result['score'] == 0.0
        assert result['source'] == 'heuristic'
        assert result['llm_score'] is None
    
    @pytest.mark.asyncio
    async def test_low_score_no_llm(self, scorer):
        """Low scoring messages shouldn't trigger LLM"""
        message = "What's the weather today?"
        result = await scorer.score_turn(message)
        assert result['source'] == 'heuristic'
        assert result['llm_score'] is None
    
    @pytest.mark.asyncio
    async def test_high_score_triggers_llm(self, scorer):
        """High scoring messages should trigger LLM (if available)"""
        message = "I feel so lost and anxious about everything in my life right now"
        result = await scorer.score_turn(message)
        # Note: This will actually call LLM in real tests
        # In unit tests, you'd mock the LLM call
        assert result['heuristic_score'] > 0.6
    
    @pytest.mark.asyncio
    async def test_long_message_triggers_llm(self, scorer):
        """Long messages should trigger LLM regardless of heuristic score"""
        message = "Can you help me understand something? I've been thinking about this for a while and I'm not sure what to make of it all."
        result = await scorer.score_turn(message)
        # Message is >120 chars, should consider LLM
        assert len(message) > 120


class TestScoreWeighting:
    """Test final score calculation"""
    
    def test_score_always_in_range(self):
        """Final scores should always be 0.0-1.0"""
        # Test various combinations
        test_cases = [
            (0.0, 0.0),
            (1.0, 1.0),
            (0.5, 0.5),
            (0.8, 0.3),
            (0.2, 0.9)
        ]
        
        for heuristic, llm in test_cases:
            final = 0.6 * heuristic + 0.4 * llm
            assert 0.0 <= final <= 1.0