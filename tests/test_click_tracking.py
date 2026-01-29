"""
Tests for click tracking and metrics logging module.

Tests cover:
- Click event logging
- Impression logging
- CTR calculation
- Rank metrics
- Response time analysis
- Variant comparison
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from services.click_tracking import (
    ClickTrackingService,
    ClickEvent,
    SearchImpression,
    get_click_tracker,
    reset_click_tracker,
    ClickSource
)


@pytest.fixture
def click_tracker():
    """Create click tracker without MongoDB."""
    reset_click_tracker()
    # Create tracker with memory-only operation (no MongoDB)
    tracker = ClickTrackingService(mongodb_uri="mongodb://invalid:invalid")
    yield tracker
    reset_click_tracker()


class TestClickEvent:
    """Tests for ClickEvent data class."""
    
    def test_click_event_creation(self):
        """Test creating a click event."""
        event = ClickEvent(
            user_id="user123",
            product_id="prod_001",
            rank=0,
            search_query="blue shoes",
            variant="search_v1",
            response_time_ms=45.2
        )
        
        assert event.user_id == "user123"
        assert event.product_id == "prod_001"
        assert event.rank == 0
        assert event.search_query == "blue shoes"
        assert event.variant == "search_v1"
        assert event.response_time_ms == 45.2
        assert event.source == ClickSource.SEARCH_RESULTS.value
    
    def test_click_event_to_dict(self):
        """Test converting click event to dict."""
        event = ClickEvent(
            user_id="user123",
            product_id="prod_001",
            rank=0,
            search_query="test",
            variant="search_v1",
            response_time_ms=50.0
        )
        
        d = event.to_dict()
        assert d["user_id"] == "user123"
        assert d["product_id"] == "prod_001"
        assert d["rank"] == 0
        assert d["search_query"] == "test"
        assert d["variant"] == "search_v1"
        assert d["response_time_ms"] == 50.0
    
    def test_click_event_with_custom_source(self):
        """Test click event with custom source."""
        event = ClickEvent(
            user_id="user123",
            product_id="prod_001",
            rank=2,
            search_query="test",
            variant="search_v2",
            response_time_ms=50.0,
            source=ClickSource.RECOMMENDATIONS.value
        )
        
        assert event.source == ClickSource.RECOMMENDATIONS.value


class TestSearchImpression:
    """Tests for SearchImpression data class."""
    
    def test_impression_creation(self):
        """Test creating a search impression."""
        impression = SearchImpression(
            user_id="user123",
            query="blue shoes",
            variant="search_v1",
            results_count=10,
            response_time_ms=45.2
        )
        
        assert impression.user_id == "user123"
        assert impression.query == "blue shoes"
        assert impression.variant == "search_v1"
        assert impression.results_count == 10
        assert impression.response_time_ms == 45.2
    
    def test_impression_to_dict(self):
        """Test converting impression to dict."""
        impression = SearchImpression(
            user_id="user123",
            query="test",
            variant="search_v2",
            results_count=5,
            response_time_ms=50.0
        )
        
        d = impression.to_dict()
        assert d["user_id"] == "user123"
        assert d["query"] == "test"
        assert d["variant"] == "search_v2"
        assert d["results_count"] == 5


class TestClickTrackingService:
    """Tests for ClickTrackingService without MongoDB."""
    
    def test_service_initialization(self, click_tracker):
        """Test initializing click tracking service."""
        assert click_tracker is not None
    
    @patch('services.click_tracking.MONGODB_AVAILABLE', False)
    def test_service_without_mongodb(self):
        """Test service behavior when MongoDB unavailable."""
        tracker = ClickTrackingService()
        
        # Should handle gracefully
        assert tracker.db is None
    
    def test_click_logging_without_db(self, click_tracker):
        """Test that click logging returns False without DB."""
        click_tracker.db = None
        
        event = ClickEvent(
            user_id="user123",
            product_id="prod_001",
            rank=0,
            search_query="test",
            variant="search_v1",
            response_time_ms=50.0
        )
        
        result = click_tracker.log_click(event)
        assert result is False
    
    def test_impression_logging_without_db(self, click_tracker):
        """Test that impression logging returns False without DB."""
        click_tracker.db = None
        
        impression = SearchImpression(
            user_id="user123",
            query="test",
            variant="search_v1",
            results_count=10,
            response_time_ms=50.0
        )
        
        result = click_tracker.log_impression(impression)
        assert result is False
    
    def test_ctr_calculation_no_db(self, click_tracker):
        """Test CTR calculation without database."""
        click_tracker.db = None
        
        metrics = click_tracker.get_ctr()
        assert metrics["ctr"] == 0.0
        assert metrics["clicks"] == 0
        assert metrics["impressions"] == 0
    
    def test_rank_metrics_no_db(self, click_tracker):
        """Test rank metrics without database."""
        click_tracker.db = None
        
        metrics = click_tracker.get_rank_metrics()
        assert metrics["avg_rank"] == 0
        assert metrics["clicks_by_rank"] == {}
    
    def test_response_time_metrics_no_db(self, click_tracker):
        """Test response time metrics without database."""
        click_tracker.db = None
        
        metrics = click_tracker.get_response_time_metrics()
        assert metrics["avg_response_time_ms"] == 0
        assert metrics["count"] == 0
    
    def test_user_summary_no_db(self, click_tracker):
        """Test user summary without database."""
        click_tracker.db = None
        
        summary = click_tracker.get_user_summary("user123")
        assert "error" in summary
        assert summary["user_id"] == "user123"
    
    def test_variant_comparison_no_db(self, click_tracker):
        """Test variant comparison without database."""
        click_tracker.db = None
        
        comparison = click_tracker.get_variant_comparison()
        assert "error" in comparison
    
    def test_reset_no_db(self, click_tracker):
        """Test reset without database."""
        click_tracker.db = None
        
        result = click_tracker.reset()
        assert result is False


class TestGlobalTracker:
    """Tests for global tracker singleton."""
    
    def test_get_click_tracker_singleton(self):
        """Test that get_click_tracker returns same instance."""
        reset_click_tracker()
        
        tracker1 = get_click_tracker()
        tracker2 = get_click_tracker()
        
        assert tracker1 is tracker2
    
    def test_reset_click_tracker(self):
        """Test resetting global tracker."""
        reset_click_tracker()
        tracker1 = get_click_tracker()
        
        reset_click_tracker()
        tracker2 = get_click_tracker()
        
        # Should be different instances after reset
        assert tracker1 is not tracker2


class TestClickEventData:
    """Tests for click event data handling."""
    
    def test_click_event_with_session(self):
        """Test click event with session ID."""
        event = ClickEvent(
            user_id="user123",
            product_id="prod_001",
            rank=0,
            search_query="test",
            variant="search_v1",
            response_time_ms=50.0,
            session_id="session_abc123"
        )
        
        assert event.session_id == "session_abc123"
        data = event.to_dict()
        assert data["session_id"] == "session_abc123"
    
    def test_click_event_timestamp(self):
        """Test that click event has timestamp."""
        event = ClickEvent(
            user_id="user123",
            product_id="prod_001",
            rank=0,
            search_query="test",
            variant="search_v1",
            response_time_ms=50.0
        )
        
        assert event.timestamp is not None
        assert isinstance(event.timestamp, datetime)
    
    def test_impression_timestamp(self):
        """Test that impression has timestamp."""
        impression = SearchImpression(
            user_id="user123",
            query="test",
            variant="search_v1",
            results_count=10,
            response_time_ms=50.0
        )
        
        assert impression.timestamp is not None
        assert isinstance(impression.timestamp, datetime)


class TestClickEventValidation:
    """Tests for click event validation."""
    
    def test_click_with_zero_rank(self):
        """Test click event with rank 0 (first result)."""
        event = ClickEvent(
            user_id="user123",
            product_id="prod_001",
            rank=0,
            search_query="test",
            variant="search_v1",
            response_time_ms=50.0
        )
        
        assert event.rank == 0
    
    def test_click_with_high_rank(self):
        """Test click event with high rank."""
        event = ClickEvent(
            user_id="user123",
            product_id="prod_001",
            rank=99,
            search_query="test",
            variant="search_v1",
            response_time_ms=50.0
        )
        
        assert event.rank == 99
    
    def test_impression_with_zero_results(self):
        """Test impression with zero results."""
        impression = SearchImpression(
            user_id="user123",
            query="test",
            variant="search_v1",
            results_count=0,
            response_time_ms=50.0
        )
        
        assert impression.results_count == 0
    
    def test_response_time_zero(self):
        """Test with zero response time."""
        event = ClickEvent(
            user_id="user123",
            product_id="prod_001",
            rank=0,
            search_query="test",
            variant="search_v1",
            response_time_ms=0.0
        )
        
        assert event.response_time_ms == 0.0


class TestVariantHandling:
    """Tests for variant-specific functionality."""
    
    def test_click_with_v1_variant(self):
        """Test click event with search_v1."""
        event = ClickEvent(
            user_id="user123",
            product_id="prod_001",
            rank=0,
            search_query="test",
            variant="search_v1",
            response_time_ms=50.0
        )
        
        assert event.variant == "search_v1"
    
    def test_click_with_v2_variant(self):
        """Test click event with search_v2."""
        event = ClickEvent(
            user_id="user123",
            product_id="prod_001",
            rank=0,
            search_query="test",
            variant="search_v2",
            response_time_ms=50.0
        )
        
        assert event.variant == "search_v2"
    
    def test_impression_with_v1_variant(self):
        """Test impression with search_v1."""
        impression = SearchImpression(
            user_id="user123",
            query="test",
            variant="search_v1",
            results_count=10,
            response_time_ms=50.0
        )
        
        assert impression.variant == "search_v1"
    
    def test_impression_with_v2_variant(self):
        """Test impression with search_v2."""
        impression = SearchImpression(
            user_id="user123",
            query="test",
            variant="search_v2",
            results_count=10,
            response_time_ms=50.0
        )
        
        assert impression.variant == "search_v2"


class TestResponseTimeHandling:
    """Tests for response time tracking."""
    
    def test_fast_response_time(self):
        """Test event with fast response time."""
        event = ClickEvent(
            user_id="user123",
            product_id="prod_001",
            rank=0,
            search_query="test",
            variant="search_v1",
            response_time_ms=10.5
        )
        
        assert event.response_time_ms == 10.5
    
    def test_slow_response_time(self):
        """Test event with slow response time."""
        event = ClickEvent(
            user_id="user123",
            product_id="prod_001",
            rank=0,
            search_query="test",
            variant="search_v1",
            response_time_ms=500.0
        )
        
        assert event.response_time_ms == 500.0
    
    def test_fractional_response_time(self):
        """Test event with fractional milliseconds."""
        event = ClickEvent(
            user_id="user123",
            product_id="prod_001",
            rank=0,
            search_query="test",
            variant="search_v1",
            response_time_ms=42.123
        )
        
        assert event.response_time_ms == 42.123
