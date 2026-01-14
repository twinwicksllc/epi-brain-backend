"""
Integration tests for depth tracking API
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.models.user import User, UserTier
from app.models.conversation import Conversation
from app.core.security import get_password_hash
import uuid

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_depth.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture
def test_user():
    """Create a test user"""
    db = TestingSessionLocal()
    user = User(
        email="test@example.com",
        password_hash=get_password_hash("testpass123"),
        tier=UserTier.PRO  # PRO tier for unlimited messages
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    yield user
    
    # Cleanup
    db.delete(user)
    db.commit()
    db.close()


@pytest.fixture
def auth_headers(test_user):
    """Get authentication headers"""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "testpass123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestDepthTracking:
    """Test depth tracking in chat API"""
    
    def test_depth_tracked_for_personal_friend(self, auth_headers):
        """Personal friend mode should track depth"""
        response = client.post(
            "/api/v1/chat/message",
            json={
                "message": "I feel so lost and anxious about everything",
                "mode": "personal_friend"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "depth" in data
        assert data["depth"] is not None
        assert 0.0 <= data["depth"] <= 1.0
    
    def test_depth_not_tracked_for_kids_learning(self, auth_headers):
        """Kids learning mode should not track depth"""
        response = client.post(
            "/api/v1/chat/message",
            json={
                "message": "Can you teach me the alphabet?",
                "mode": "kids_learning"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["depth"] is None
    
    def test_depth_increases_with_deep_messages(self, auth_headers):
        """Depth should increase with introspective messages"""
        # First message
        response1 = client.post(
            "/api/v1/chat/message",
            json={
                "message": "Hi there",
                "mode": "personal_friend"
            },
            headers=auth_headers
        )
        depth1 = response1.json()["depth"]
        conversation_id = response1.json()["conversation_id"]
        
        # Second deep message
        response2 = client.post(
            "/api/v1/chat/message",
            json={
                "message": "I feel so lost and anxious. I'm questioning my purpose and wondering why I feel this way.",
                "mode": "personal_friend",
                "conversation_id": conversation_id
            },
            headers=auth_headers
        )
        depth2 = response2.json()["depth"]
        
        # Depth should increase
        assert depth2 > depth1


class TestDepthEndpoints:
    """Test depth-specific endpoints"""
    
    def test_get_conversation_depth(self, auth_headers):
        """Should retrieve conversation depth"""
        # Create a conversation
        response = client.post(
            "/api/v1/chat/message",
            json={
                "message": "I feel anxious",
                "mode": "personal_friend"
            },
            headers=auth_headers
        )
        conversation_id = response.json()["conversation_id"]
        
        # Get depth
        depth_response = client.get(
            f"/api/v1/chat/conversations/{conversation_id}/depth",
            headers=auth_headers
        )
        
        assert depth_response.status_code == 200
        data = depth_response.json()
        assert "depth" in data
        assert "enabled" in data
        assert data["enabled"] is True
    
    def test_disable_depth_tracking(self, auth_headers):
        """Should disable depth tracking"""
        # Create a conversation
        response = client.post(
            "/api/v1/chat/message",
            json={
                "message": "I feel anxious",
                "mode": "personal_friend"
            },
            headers=auth_headers
        )
        conversation_id = response.json()["conversation_id"]
        
        # Disable depth
        disable_response = client.post(
            f"/api/v1/chat/conversations/{conversation_id}/depth/disable",
            headers=auth_headers
        )
        
        assert disable_response.status_code == 200
        
        # Verify depth is disabled
        depth_response = client.get(
            f"/api/v1/chat/conversations/{conversation_id}/depth",
            headers=auth_headers
        )
        assert depth_response.json()["enabled"] is False
    
    def test_enable_depth_tracking(self, auth_headers):
        """Should enable depth tracking"""
        # Create a conversation and disable depth
        response = client.post(
            "/api/v1/chat/message",
            json={
                "message": "Hello",
                "mode": "personal_friend"
            },
            headers=auth_headers
        )
        conversation_id = response.json()["conversation_id"]
        
        client.post(
            f"/api/v1/chat/conversations/{conversation_id}/depth/disable",
            headers=auth_headers
        )
        
        # Re-enable depth
        enable_response = client.post(
            f"/api/v1/chat/conversations/{conversation_id}/depth/enable",
            headers=auth_headers
        )
        
        assert enable_response.status_code == 200
        
        # Verify depth is enabled
        depth_response = client.get(
            f"/api/v1/chat/conversations/{conversation_id}/depth",
            headers=auth_headers
        )
        assert depth_response.json()["enabled"] is True
    
    def test_cannot_enable_depth_for_unsupported_mode(self, auth_headers):
        """Should not allow enabling depth for unsupported modes"""
        # Create a conversation with kids_learning mode
        response = client.post(
            "/api/v1/chat/message",
            json={
                "message": "Teach me ABCs",
                "mode": "kids_learning"
            },
            headers=auth_headers
        )
        conversation_id = response.json()["conversation_id"]
        
        # Try to enable depth
        enable_response = client.post(
            f"/api/v1/chat/conversations/{conversation_id}/depth/enable",
            headers=auth_headers
        )
        
        assert enable_response.status_code == 400
        assert "not available" in enable_response.json()["detail"]


# Cleanup test database after all tests
def teardown_module(module):
    """Clean up test database"""
    import os
    if os.path.exists("./test_depth.db"):
        os.remove("./test_depth.db")