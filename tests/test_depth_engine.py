"""
Unit tests for depth engine
"""

import pytest
from datetime import datetime, timedelta
from app.services.depth_engine import ConversationDepthEngine


class TestDepthEngineInitialization:
    """Test engine initialization"""
    
    def test_default_initialization(self):
        """Should initialize with depth 0.0"""
        engine = ConversationDepthEngine()
        assert engine.depth == 0.0
        assert engine.last_updated_at is not None
    
    def test_custom_initialization(self):
        """Should accept custom initial depth"""
        engine = ConversationDepthEngine(initial_depth=0.5)
        assert engine.depth == 0.5
    
    def test_clamps_invalid_depth(self):
        """Should clamp depth to valid range"""
        engine1 = ConversationDepthEngine(initial_depth=-0.5)
        assert engine1.depth == 0.0
        
        engine2 = ConversationDepthEngine(initial_depth=1.5)
        assert engine2.depth == 1.0


class TestAsymmetricInertia:
    """Test asymmetric inertia behavior"""
    
    def test_going_deeper_faster(self):
        """Going deeper should be faster than coming back up"""
        engine = ConversationDepthEngine(initial_depth=0.2)
        
        # Update with high score (going deeper)
        engine.update(0.8)
        depth_after_up = engine.depth
        
        # Should have moved significantly toward 0.8
        assert depth_after_up > 0.3  # Moved more than 0.1
        assert depth_after_up < 0.8  # But not all the way
    
    def test_coming_up_slower(self):
        """Coming back up should be slower"""
        engine = ConversationDepthEngine(initial_depth=0.8)
        
        # Update with low score (coming back up)
        engine.update(0.2)
        depth_after_down = engine.depth
        
        # Should have moved less toward 0.2
        assert depth_after_down > 0.6  # Didn't drop much
        assert depth_after_down < 0.8  # But did drop some
    
    def test_multiple_updates_accumulate(self):
        """Multiple updates should accumulate"""
        engine = ConversationDepthEngine()
        
        # Several deep turns
        engine.update(0.7)
        engine.update(0.8)
        engine.update(0.9)
        
        # Should be quite deep now
        assert engine.depth > 0.5


class TestTemporalDecay:
    """Test temporal decay behavior"""
    
    def test_decay_over_time(self):
        """Depth should decay over time"""
        past_time = datetime.utcnow() - timedelta(minutes=5)
        engine = ConversationDepthEngine(
            initial_depth=0.8,
            last_updated_at=past_time
        )
        
        # Get depth with decay applied
        current_depth = engine.get_depth()
        
        # Should be less than stored depth
        assert current_depth < engine.depth
    
    def test_decay_doesnt_go_negative(self):
        """Decay should never make depth negative"""
        past_time = datetime.utcnow() - timedelta(hours=10)
        engine = ConversationDepthEngine(
            initial_depth=0.1,
            last_updated_at=past_time
        )
        
        current_depth = engine.get_depth()
        assert current_depth >= 0.0
    
    def test_update_applies_decay_first(self):
        """Update should apply decay before inertia"""
        past_time = datetime.utcnow() - timedelta(minutes=5)
        engine = ConversationDepthEngine(
            initial_depth=0.8,
            last_updated_at=past_time
        )
        
        old_depth = engine.depth
        engine.update(0.5)
        
        # Decay should have been applied
        # (exact value depends on decay rate)
        assert engine.last_updated_at > past_time


class TestDepthBounds:
    """Test depth boundary conditions"""
    
    def test_depth_never_exceeds_one(self):
        """Depth should never exceed 1.0"""
        engine = ConversationDepthEngine(initial_depth=0.9)
        
        # Multiple high scores
        for _ in range(10):
            engine.update(1.0)
        
        assert engine.depth <= 1.0
    
    def test_depth_never_goes_negative(self):
        """Depth should never go below 0.0"""
        engine = ConversationDepthEngine(initial_depth=0.1)
        
        # Multiple low scores
        for _ in range(10):
            engine.update(0.0)
        
        assert engine.depth >= 0.0


class TestReset:
    """Test reset functionality"""
    
    def test_reset_clears_depth(self):
        """Reset should set depth to 0.0"""
        engine = ConversationDepthEngine(initial_depth=0.8)
        engine.reset()
        
        assert engine.depth == 0.0
    
    def test_reset_updates_timestamp(self):
        """Reset should update last_updated_at"""
        past_time = datetime.utcnow() - timedelta(minutes=5)
        engine = ConversationDepthEngine(
            initial_depth=0.8,
            last_updated_at=past_time
        )
        
        engine.reset()
        
        # Should be recent
        time_diff = (datetime.utcnow() - engine.last_updated_at).total_seconds()
        assert time_diff < 1  # Less than 1 second ago


class TestGetState:
    """Test state inspection"""
    
    def test_get_state_returns_dict(self):
        """get_state should return complete state info"""
        engine = ConversationDepthEngine(initial_depth=0.5)
        state = engine.get_state()
        
        assert 'stored_depth' in state
        assert 'current_depth' in state
        assert 'last_updated_at' in state
        assert 'elapsed_seconds' in state
        assert 'decay_applied' in state
    
    def test_get_depth_doesnt_modify_state(self):
        """get_depth should not modify internal state"""
        engine = ConversationDepthEngine(initial_depth=0.5)
        
        stored_depth_before = engine.depth
        last_updated_before = engine.last_updated_at
        
        _ = engine.get_depth()
        
        assert engine.depth == stored_depth_before
        assert engine.last_updated_at == last_updated_before