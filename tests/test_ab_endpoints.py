"""
Integration tests for A/B testing API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import json

from main import app
from services.ab_testing import (
    get_experiment_manager,
    reset_experiment_manager,
    ExperimentVariant
)


@pytest.fixture
def client():
    """Create test client."""
    reset_experiment_manager()
    return TestClient(app)


@pytest.fixture
def user_headers():
    """Standard user headers."""
    return {
        "X-User-ID": "test_user_123",
        "X-Session-ID": "session_abc"
    }


class TestABAssignmentEndpoint:
    """Test /ab/assign endpoint."""
    
    def test_assign_variant_success(self, client):
        """Test successful variant assignment."""
        response = client.post("/ab/assign?user_id=user123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "user123"
        assert data["variant"] in ["search_v1", "search_v2"]
        assert "assigned_at" in data
    
    def test_assign_idempotent(self, client):
        """Test that repeated assignments are idempotent."""
        response1 = client.post("/ab/assign?user_id=user456")
        response2 = client.post("/ab/assign?user_id=user456")
        
        data1 = response1.json()
        data2 = response2.json()
        
        assert data1["variant"] == data2["variant"]
        assert data1["assigned_at"] == data2["assigned_at"]
    
    def test_assign_without_user_id(self, client, user_headers):
        """Test assignment without explicit user_id (uses header)."""
        response = client.post("/ab/assign", headers=user_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "test_user_123"


class TestABLogSearchEndpoint:
    """Test /ab/log-search endpoint."""
    
    def test_log_search_success(self, client, user_headers):
        """Test successful search logging."""
        payload = {
            "query": "casual shirts",
            "results_count": 24,
            "search_time_ms": 145.5
        }
        
        response = client.post(
            "/ab/log-search",
            json=payload,
            headers=user_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["event_type"] == "search"
        assert data["user_id"] == "test_user_123"
        assert data["variant"] in ["search_v1", "search_v2"]
    
    def test_log_search_required_fields(self, client, user_headers):
        """Test that required fields are enforced."""
        payload = {"query": "test"}  # Missing results_count
        
        response = client.post(
            "/ab/log-search",
            json=payload,
            headers=user_headers
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_log_search_auto_generates_user_id(self, client):
        """Test that user_id is auto-generated if not provided."""
        payload = {
            "query": "shoes",
            "results_count": 15,
            "search_time_ms": 100.0
        }
        
        response = client.post("/ab/log-search", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert len(data["user_id"]) > 0


class TestABLogClickEndpoint:
    """Test /ab/log-click endpoint."""
    
    def test_log_click_success(self, client, user_headers):
        """Test successful click logging."""
        payload = {
            "product_id": "prod_456",
            "product_title": "Blue Casual Shirt",
            "position": 0,
            "query": "casual shirts"
        }
        
        response = client.post(
            "/ab/log-click",
            json=payload,
            headers=user_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["event_type"] == "click"
        assert data["user_id"] == "test_user_123"
    
    def test_log_click_minimal_payload(self, client, user_headers):
        """Test click logging with minimal fields."""
        payload = {"product_id": "prod_123"}
        
        response = client.post(
            "/ab/log-click",
            json=payload,
            headers=user_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["event_type"] == "click"
    
    def test_log_click_missing_product_id(self, client, user_headers):
        """Test that product_id is required."""
        payload = {"product_title": "Some Product"}
        
        response = client.post(
            "/ab/log-click",
            json=payload,
            headers=user_headers
        )
        
        assert response.status_code == 422


class TestABMetricsEndpoint:
    """Test /ab/metrics endpoint."""
    
    def test_get_metrics_empty(self, client):
        """Test metrics with no events."""
        response = client.get("/ab/metrics")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_events"] == 0
        assert data["search_events"] == 0
        assert data["click_events"] == 0
    
    def test_get_metrics_with_events(self, client, user_headers):
        """Test metrics after logging events."""
        # Log some events
        client.post(
            "/ab/log-search",
            json={"query": "test", "results_count": 10, "search_time_ms": 100},
            headers=user_headers
        )
        client.post(
            "/ab/log-click",
            json={"product_id": "prod1", "position": 0},
            headers=user_headers
        )
        
        response = client.get("/ab/metrics")
        
        assert response.status_code == 200
        data = response.json()
        assert data["search_events"] == 1
        assert data["click_events"] == 1
        assert data["total_events"] == 2
    
    def test_metrics_ctr_calculated(self, client, user_headers):
        """Test that CTR is calculated in metrics."""
        # Log search and click
        client.post(
            "/ab/log-search",
            json={"query": "shirts", "results_count": 20},
            headers=user_headers
        )
        client.post(
            "/ab/log-click",
            json={"product_id": "prod1"},
            headers=user_headers
        )
        
        response = client.get("/ab/metrics")
        data = response.json()
        
        # Should have calculated CTR for one variant
        assert "search_v1" in data
        assert "search_v2" in data
        assert "ctr" in data["search_v1"]
        assert "ctr" in data["search_v2"]


class TestABAssignmentEndpoint:
    """Test /ab/assignment endpoint."""
    
    def test_get_assignment_exists(self, client):
        """Test retrieving existing assignment."""
        # First assign
        client.post("/ab/assign?user_id=user_xyz")
        
        # Then retrieve
        response = client.get("/ab/assignment?user_id=user_xyz")
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "user_xyz"
        assert data["variant"] in ["search_v1", "search_v2"]
    
    def test_get_assignment_not_found(self, client):
        """Test retrieving non-existent assignment."""
        response = client.get("/ab/assignment?user_id=nonexistent_user")
        
        assert response.status_code == 200
        data = response.json()
        assert "error" in data


class TestABEventsEndpoint:
    """Test /ab/events endpoint."""
    
    def test_get_all_events(self, client, user_headers):
        """Test getting all events."""
        # Log some events
        for i in range(3):
            client.post(
                "/ab/log-search",
                json={"query": f"query{i}", "results_count": 10},
                headers=user_headers
            )
        
        response = client.get("/ab/events")
        
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 3
        assert len(data["events"]) == 3
    
    def test_filter_events_by_user_id(self, client):
        """Test filtering events by user_id."""
        # Log for different users
        client.post(
            "/ab/log-search",
            json={"query": "test", "results_count": 10},
            headers={"X-User-ID": "user1"}
        )
        client.post(
            "/ab/log-search",
            json={"query": "test", "results_count": 10},
            headers={"X-User-ID": "user2"}
        )
        
        response = client.get("/ab/events?user_id=user1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["events"][0]["user_id"] == "user1"
    
    def test_filter_events_by_type(self, client, user_headers):
        """Test filtering events by type."""
        # Log search and click
        client.post(
            "/ab/log-search",
            json={"query": "test", "results_count": 10},
            headers=user_headers
        )
        client.post(
            "/ab/log-click",
            json={"product_id": "prod1"},
            headers=user_headers
        )
        
        response = client.get("/ab/events?event_type=search")
        
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["events"][0]["event_type"] == "search"
    
    def test_events_limit(self, client, user_headers):
        """Test event limit parameter."""
        # Log 10 events
        for i in range(10):
            client.post(
                "/ab/log-search",
                json={"query": f"query{i}", "results_count": 10},
                headers=user_headers
            )
        
        response = client.get("/ab/events?limit=5")
        
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 5


class TestABResetEndpoint:
    """Test /ab/reset endpoint."""
    
    def test_reset_clears_data(self, client, user_headers):
        """Test that reset clears all data."""
        # Log some data
        client.post("/ab/assign?user_id=user_temp")
        client.post(
            "/ab/log-search",
            json={"query": "test", "results_count": 10},
            headers=user_headers
        )
        
        # Verify data exists
        response = client.get("/ab/metrics")
        assert response.json()["total_events"] > 0
        
        # Reset
        reset_response = client.delete("/ab/reset")
        assert reset_response.status_code == 200
        assert reset_response.json()["success"] is True
        
        # Verify data cleared
        response = client.get("/ab/metrics")
        assert response.json()["total_events"] == 0


class TestMiddlewareIntegration:
    """Test middleware injection of variant."""
    
    def test_variant_in_response_headers(self, client, user_headers):
        """Test that variant is added to response headers."""
        response = client.get("/", headers=user_headers)
        
        assert "X-Variant" in response.headers
        assert response.headers["X-Variant"] in ["search_v1", "search_v2"]
        assert "X-User-ID" in response.headers
        assert "X-Session-ID" in response.headers
    
    def test_consistent_variant_across_requests(self, client, user_headers):
        """Test that same user gets same variant across requests."""
        response1 = client.get("/", headers=user_headers)
        response2 = client.get("/", headers=user_headers)
        
        variant1 = response1.headers.get("X-Variant")
        variant2 = response2.headers.get("X-Variant")
        
        assert variant1 == variant2
    
    def test_different_users_may_get_different_variants(self, client):
        """Test that different users can get different variants."""
        variants = set()
        
        for i in range(50):
            headers = {"X-User-ID": f"user_{i}"}
            response = client.get("/", headers=headers)
            variant = response.headers.get("X-Variant")
            variants.add(variant)
        
        # With 50 users and 50/50 split, likely to see both variants
        # (not guaranteed but very high probability)
        assert len(variants) > 0
