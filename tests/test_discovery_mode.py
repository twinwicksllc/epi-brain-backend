import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_discovery_mode_no_auth_required():
    """Test that discovery mode works without authentication"""
    response = client.post(
        "/api/v1/chat/message",
        json={
            "message": "Hello, I want to learn about EPI Brain",
            "mode": "discovery"
        }
    )
    # Should NOT return 401 Unauthorized (authentication is not required)
    # May return 503 if AI API is not configured, which is expected in test env
    assert response.status_code != 401
    # Check that it's not an authentication error
    if response.status_code != 200:
        data = response.json()
        assert "Authentication" not in str(data.get("detail", ""))

def test_discovery_mode_requires_mode_parameter():
    """Test that discovery mode is used when no mode is specified"""
    response = client.post(
        "/api/v1/chat/message",
        json={
            "message": "Hello"
        }
    )
    # Should default to discovery mode when no mode is specified
    # Should NOT return 401 Unauthorized (authentication is not required for discovery)
    # May return 503 if AI API is not configured, which is expected in test env
    assert response.status_code != 401
    # Check that it's not an authentication error
    if response.status_code != 200:
        data = response.json()
        assert "Authentication" not in str(data.get("detail", ""))

def test_authenticated_mode_requires_auth():
    """Test that non-discovery modes require authentication"""
    response = client.post(
        "/api/v1/chat/message",
        json={
            "message": "Hello",
            "mode": "personal_friend"
        }
    )
    # Should return 401 Unauthorized for authenticated modes
    assert response.status_code == 401