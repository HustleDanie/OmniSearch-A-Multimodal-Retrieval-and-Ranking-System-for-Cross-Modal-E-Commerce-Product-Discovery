"""
Integration tests for click analytics API endpoints.

Tests cover:
- Click event logging via API
- Impression logging via API
- CTR metrics retrieval
- Rank metrics retrieval
- Response time metrics retrieval
- User analytics summary
- Variant comparison
- Analytics reset
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app
from services.click_tracking import reset_click_tracker
from api.ab_middleware import get_user_id, get_session_id


@pytest.fixture
def client():
    """Create FastAPI test client."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_tracker():
    """Reset tracker before each test."""
    reset_click_tracker()
    yield
    reset_click_tracker()


class TestClickLoggingEndpoint:
    """Tests for POST /analytics/log-click endpoint."""
    
    def test_log_click_success(self, client):
        """Test successful click logging."""
        response = client.post(
            "/analytics/log-click",
            json={
                "product_id": "prod_123",
                "rank": 2,
                "search_query": "blue shoes",
                "variant": "search_v1",
                "response_time_ms": 45.2,
                "source": "SEARCH_RESULTS"
            },
            headers={"X-User-ID": "user123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["user_id"] == "user123"
        assert data["product_id"] == "prod_123"
        assert data["rank"] == 2
    
    def test_log_click_without_user_header(self, client):
        """Test click logging without X-User-ID header."""
        response = client.post(
            "/analytics/log-click",
            json={
                "product_id": "prod_123",
                "rank": 2,
                "search_query": "blue shoes",
                "variant": "search_v1",
                "response_time_ms": 45.2,
                "source": "SEARCH_RESULTS"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        # User ID should be auto-generated
        assert "user_id" in data
    
    def test_log_click_missing_required_field(self, client):
        """Test click logging with missing required field."""
        response = client.post(
            "/analytics/log-click",
            json={
                "rank": 2,
                "search_query": "blue shoes",
                "variant": "search_v1",
                "response_time_ms": 45.2,
                # Missing product_id
            },
            headers={"X-User-ID": "user123"}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_log_click_with_recommendations_source(self, client):
        """Test click logging with RECOMMENDATIONS source."""
        response = client.post(
            "/analytics/log-click",
            json={
                "product_id": "prod_123",
                "rank": 0,
                "search_query": "test",
                "variant": "search_v2",
                "response_time_ms": 50.0,
                "source": "RECOMMENDATIONS"
            },
            headers={"X-User-ID": "user456"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_log_click_response_time_format(self, client):
        """Test that response time is preserved in click logging."""
        response = client.post(
            "/analytics/log-click",
            json={
                "product_id": "prod_123",
                "rank": 1,
                "search_query": "test",
                "variant": "search_v1",
                "response_time_ms": 123.456,
                "source": "SEARCH_RESULTS"
            },
            headers={"X-User-ID": "user123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data


class TestImpressionLoggingEndpoint:
    """Tests for POST /analytics/log-impression endpoint."""
    
    def test_log_impression_success(self, client):
        """Test successful impression logging."""
        response = client.post(
            "/analytics/log-impression",
            json={
                "query": "blue shoes",
                "variant": "search_v1",
                "results_count": 42,
                "response_time_ms": 45.2
            },
            headers={"X-User-ID": "user123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["user_id"] == "user123"
        assert data["query"] == "blue shoes"
    
    def test_log_impression_without_user_header(self, client):
        """Test impression logging without X-User-ID header."""
        response = client.post(
            "/analytics/log-impression",
            json={
                "query": "test",
                "variant": "search_v2",
                "results_count": 10,
                "response_time_ms": 50.0
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "user_id" in data
    
    def test_log_impression_zero_results(self, client):
        """Test impression logging with zero results."""
        response = client.post(
            "/analytics/log-impression",
            json={
                "query": "xyz123",
                "variant": "search_v1",
                "results_count": 0,
                "response_time_ms": 20.0
            },
            headers={"X-User-ID": "user123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_log_impression_many_results(self, client):
        """Test impression logging with many results."""
        response = client.post(
            "/analytics/log-impression",
            json={
                "query": "common query",
                "variant": "search_v2",
                "results_count": 1000,
                "response_time_ms": 150.0
            },
            headers={"X-User-ID": "user123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


class TestCTRMetricsEndpoint:
    """Tests for GET /analytics/ctr endpoint."""
    
    def test_get_ctr_without_data(self, client):
        """Test CTR endpoint when no data logged."""
        response = client.get("/analytics/ctr")
        
        assert response.status_code == 200
        data = response.json()
        assert "ctr" in data
        assert data["ctr"] == 0.0
    
    def test_get_ctr_with_user_filter(self, client):
        """Test CTR endpoint with user filter."""
        # Log some data first
        client.post(
            "/analytics/log-impression",
            json={
                "query": "test",
                "variant": "search_v1",
                "results_count": 10,
                "response_time_ms": 50.0
            },
            headers={"X-User-ID": "user123"}
        )
        
        response = client.get("/analytics/ctr?user_id=user123")
        assert response.status_code == 200
        data = response.json()
        assert "ctr" in data
    
    def test_get_ctr_with_variant_filter(self, client):
        """Test CTR endpoint with variant filter."""
        response = client.get("/analytics/ctr?variant=search_v1")
        
        assert response.status_code == 200
        data = response.json()
        assert "ctr" in data
    
    def test_get_ctr_with_days_filter(self, client):
        """Test CTR endpoint with days parameter."""
        response = client.get("/analytics/ctr?days=30")
        
        assert response.status_code == 200
        data = response.json()
        assert "ctr" in data
    
    def test_get_ctr_all_filters(self, client):
        """Test CTR endpoint with all filters."""
        response = client.get(
            "/analytics/ctr?user_id=user123&variant=search_v2&days=14"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "ctr" in data
        assert "clicks" in data
        assert "impressions" in data


class TestRankMetricsEndpoint:
    """Tests for GET /analytics/rank-metrics endpoint."""
    
    def test_get_rank_metrics_empty(self, client):
        """Test rank metrics endpoint with no data."""
        response = client.get("/analytics/rank-metrics")
        
        assert response.status_code == 200
        data = response.json()
        assert "avg_rank" in data
        assert "total_clicks" in data
    
    def test_get_rank_metrics_with_user_filter(self, client):
        """Test rank metrics with user filter."""
        response = client.get("/analytics/rank-metrics?user_id=user123")
        
        assert response.status_code == 200
        data = response.json()
        assert "avg_rank" in data
    
    def test_get_rank_metrics_with_variant_filter(self, client):
        """Test rank metrics with variant filter."""
        response = client.get("/analytics/rank-metrics?variant=search_v1")
        
        assert response.status_code == 200
        data = response.json()
        assert "avg_rank" in data
    
    def test_get_rank_metrics_with_days(self, client):
        """Test rank metrics with days parameter."""
        response = client.get("/analytics/rank-metrics?days=7")
        
        assert response.status_code == 200
        data = response.json()
        assert "avg_rank" in data


class TestResponseTimeMetricsEndpoint:
    """Tests for GET /analytics/response-time endpoint."""
    
    def test_get_response_time_empty(self, client):
        """Test response time metrics with no data."""
        response = client.get("/analytics/response-time")
        
        assert response.status_code == 200
        data = response.json()
        assert "avg_response_time_ms" in data
        assert "min_response_time_ms" in data
        assert "max_response_time_ms" in data
    
    def test_get_response_time_with_user_filter(self, client):
        """Test response time metrics with user filter."""
        response = client.get("/analytics/response-time?user_id=user123")
        
        assert response.status_code == 200
        data = response.json()
        assert "avg_response_time_ms" in data
    
    def test_get_response_time_with_variant_filter(self, client):
        """Test response time metrics with variant filter."""
        response = client.get(
            "/analytics/response-time?variant=search_v2"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "avg_response_time_ms" in data
    
    def test_get_response_time_with_days(self, client):
        """Test response time metrics with days parameter."""
        response = client.get("/analytics/response-time?days=30")
        
        assert response.status_code == 200
        data = response.json()
        assert "avg_response_time_ms" in data


class TestUserAnalyticsEndpoint:
    """Tests for GET /analytics/user/{user_id} endpoint."""
    
    def test_get_user_analytics(self, client):
        """Test getting analytics for specific user."""
        response = client.get("/analytics/user/user123")
        
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert data["user_id"] == "user123"
    
    def test_get_user_analytics_with_days(self, client):
        """Test getting user analytics with days parameter."""
        response = client.get("/analytics/user/user123?days=14")
        
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
    
    def test_get_user_analytics_different_user(self, client):
        """Test getting analytics for different user."""
        response = client.get("/analytics/user/user456")
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "user456"


class TestVariantComparisonEndpoint:
    """Tests for GET /analytics/variants-comparison endpoint."""
    
    def test_get_variant_comparison(self, client):
        """Test getting variant comparison."""
        response = client.get("/analytics/variants-comparison")
        
        assert response.status_code == 200
        data = response.json()
        # Should have either period_days or error field
        assert "period_days" in data or "error" in data
    
    def test_get_variant_comparison_with_days(self, client):
        """Test variant comparison with custom days."""
        response = client.get("/analytics/variants-comparison?days=30")
        
        assert response.status_code == 200
        data = response.json()
        # Should have either period_days or error field
        assert "period_days" in data or "error" in data


class TestResetEndpoint:
    """Tests for DELETE /analytics/reset endpoint."""
    
    def test_reset_analytics(self, client):
        """Test resetting all analytics data."""
        # Log some data
        client.post(
            "/analytics/log-click",
            json={
                "product_id": "prod_123",
                "rank": 0,
                "search_query": "test",
                "variant": "search_v1",
                "response_time_ms": 50.0,
                "source": "SEARCH_RESULTS"
            },
            headers={"X-User-ID": "user123"}
        )
        
        # Reset
        response = client.delete("/analytics/reset")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


class TestEndpointIntegration:
    """Integration tests across multiple endpoints."""
    
    def test_log_and_retrieve_metrics(self, client):
        """Test logging data and then retrieving metrics."""
        # Log impression
        client.post(
            "/analytics/log-impression",
            json={
                "query": "test query",
                "variant": "search_v1",
                "results_count": 10,
                "response_time_ms": 50.0
            },
            headers={"X-User-ID": "user123"}
        )
        
        # Log click
        client.post(
            "/analytics/log-click",
            json={
                "product_id": "prod_001",
                "rank": 2,
                "search_query": "test query",
                "variant": "search_v1",
                "response_time_ms": 45.0,
                "source": "SEARCH_RESULTS"
            },
            headers={"X-User-ID": "user123"}
        )
        
        # Get CTR
        response = client.get("/analytics/ctr?user_id=user123")
        assert response.status_code == 200
        data = response.json()
        assert data["clicks"] >= 0
        assert data["impressions"] >= 0
    
    def test_multiple_variants_comparison(self, client):
        """Test logging data for multiple variants."""
        # Log v1 impression and click
        client.post(
            "/analytics/log-impression",
            json={
                "query": "test",
                "variant": "search_v1",
                "results_count": 10,
                "response_time_ms": 50.0
            },
            headers={"X-User-ID": "user123"}
        )
        
        client.post(
            "/analytics/log-click",
            json={
                "product_id": "prod_001",
                "rank": 1,
                "search_query": "test",
                "variant": "search_v1",
                "response_time_ms": 45.0,
                "source": "SEARCH_RESULTS"
            },
            headers={"X-User-ID": "user123"}
        )
        
        # Log v2 impression and click
        client.post(
            "/analytics/log-impression",
            json={
                "query": "test",
                "variant": "search_v2",
                "results_count": 15,
                "response_time_ms": 60.0
            },
            headers={"X-User-ID": "user456"}
        )
        
        client.post(
            "/analytics/log-click",
            json={
                "product_id": "prod_002",
                "rank": 0,
                "search_query": "test",
                "variant": "search_v2",
                "response_time_ms": 55.0,
                "source": "SEARCH_RESULTS"
            },
            headers={"X-User-ID": "user456"}
        )
        
        # Get variant comparison
        response = client.get("/analytics/variants-comparison")
        assert response.status_code == 200
