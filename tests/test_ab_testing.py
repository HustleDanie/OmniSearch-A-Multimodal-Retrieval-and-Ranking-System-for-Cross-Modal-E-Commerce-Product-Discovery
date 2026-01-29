"""
Tests for A/B testing module.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from services.ab_testing import (
    ExperimentManager,
    ExperimentVariant,
    ExperimentAssignment,
    SearchEvent,
    ClickEvent,
    get_experiment_manager,
    reset_experiment_manager
)


@pytest.fixture
def manager():
    """Create a fresh experiment manager for each test."""
    reset_experiment_manager()
    return ExperimentManager(storage_backend="memory")


@pytest.fixture
def user_id():
    """Test user ID."""
    return "test_user_123"


class TestExperimentAssignment:
    """Test user variant assignment."""
    
    def test_assign_variant_returns_valid_variant(self, manager, user_id):
        """Test that assignment returns one of the valid variants."""
        assignment = manager.assign_variant(user_id)
        
        assert assignment.user_id == user_id
        assert assignment.variant in [ExperimentVariant.SEARCH_V1, ExperimentVariant.SEARCH_V2]
        assert isinstance(assignment.assigned_at, datetime)
    
    def test_assign_variant_idempotent(self, manager, user_id):
        """Test that assigning same user twice returns same variant."""
        assignment1 = manager.assign_variant(user_id)
        assignment2 = manager.assign_variant(user_id)
        
        assert assignment1.variant == assignment2.variant
        assert assignment1.assigned_at == assignment2.assigned_at
    
    def test_assign_variant_with_metadata(self, manager, user_id):
        """Test assigning variant with metadata."""
        metadata = {"device": "mobile", "location": "US"}
        assignment = manager.assign_variant(user_id, metadata=metadata)
        
        assert assignment.metadata == metadata
    
    def test_get_assignment_exists(self, manager, user_id):
        """Test retrieving existing assignment."""
        assigned = manager.assign_variant(user_id)
        retrieved = manager.get_assignment(user_id)
        
        assert retrieved is not None
        assert retrieved.user_id == assigned.user_id
        assert retrieved.variant == assigned.variant
    
    def test_get_assignment_not_exists(self, manager):
        """Test retrieving non-existent assignment."""
        result = manager.get_assignment("nonexistent")
        assert result is None
    
    def test_split_ratio_respected(self, manager):
        """Test that split ratio is approximately respected."""
        # Set 70% to v1, 30% to v2
        manager.split_ratio = 0.7
        
        assignments = []
        for i in range(100):
            assignment = manager.assign_variant(f"user_{i}")
            assignments.append(assignment.variant)
        
        v1_count = sum(1 for v in assignments if v == ExperimentVariant.SEARCH_V1)
        v1_ratio = v1_count / len(assignments)
        
        # Allow 10% deviation from expected 70%
        assert 0.6 < v1_ratio < 0.8


class TestSearchEvent:
    """Test search event logging."""
    
    def test_log_search_creates_event(self, manager, user_id):
        """Test logging a search event."""
        event = manager.log_search(
            user_id=user_id,
            query="casual shirts",
            results_count=24,
            search_time_ms=145.5
        )
        
        assert isinstance(event, SearchEvent)
        assert event.user_id == user_id
        assert event.query == "casual shirts"
        assert event.results_count == 24
        assert event.search_time_ms == 145.5
        assert event.event_type == "search"
    
    def test_log_search_with_session(self, manager, user_id):
        """Test logging search with session ID."""
        session_id = "sess_123"
        event = manager.log_search(
            user_id=user_id,
            query="blue jeans",
            results_count=10,
            session_id=session_id
        )
        
        assert event.session_id == session_id
    
    def test_log_search_auto_assigns_variant(self, manager, user_id):
        """Test that search logging auto-assigns variant if not exists."""
        event = manager.log_search(
            user_id=user_id,
            query="shoes",
            results_count=5
        )
        
        # Should have variant assigned
        assert event.variant in [ExperimentVariant.SEARCH_V1, ExperimentVariant.SEARCH_V2]
        
        # User should now be in assignments
        assignment = manager.get_assignment(user_id)
        assert assignment is not None
    
    def test_search_event_to_dict(self, manager, user_id):
        """Test SearchEvent serialization."""
        event = manager.log_search(
            user_id=user_id,
            query="test query",
            results_count=15,
            search_time_ms=100.0
        )
        
        d = event.to_dict()
        assert d["user_id"] == user_id
        assert d["query"] == "test query"
        assert d["results_count"] == 15
        assert d["search_time_ms"] == 100.0
        assert d["event_type"] == "search"
        assert "timestamp" in d


class TestClickEvent:
    """Test click event logging."""
    
    def test_log_click_creates_event(self, manager, user_id):
        """Test logging a click event."""
        event = manager.log_click(
            user_id=user_id,
            product_id="prod_456",
            product_title="Blue Casual Shirt",
            position=0
        )
        
        assert isinstance(event, ClickEvent)
        assert event.user_id == user_id
        assert event.product_id == "prod_456"
        assert event.product_title == "Blue Casual Shirt"
        assert event.position == 0
        assert event.event_type == "click"
    
    def test_log_click_with_query(self, manager, user_id):
        """Test logging click with original query."""
        event = manager.log_click(
            user_id=user_id,
            product_id="prod_789",
            query="casual shirts",
            position=2
        )
        
        assert event.query == "casual shirts"
    
    def test_log_click_auto_assigns(self, manager, user_id):
        """Test that click logging auto-assigns variant."""
        event = manager.log_click(
            user_id=user_id,
            product_id="prod_123"
        )
        
        # Should have variant
        assert event.variant is not None
        
        # User should be assigned
        assignment = manager.get_assignment(user_id)
        assert assignment is not None
    
    def test_click_event_to_dict(self, manager, user_id):
        """Test ClickEvent serialization."""
        event = manager.log_click(
            user_id=user_id,
            product_id="prod_999",
            product_title="Product",
            position=1,
            query="search term"
        )
        
        d = event.to_dict()
        assert d["user_id"] == user_id
        assert d["product_id"] == "prod_999"
        assert d["product_title"] == "Product"
        assert d["position"] == 1
        assert d["event_type"] == "click"


class TestMetrics:
    """Test metrics aggregation."""
    
    def test_get_metrics_empty(self, manager):
        """Test metrics with no events."""
        metrics = manager.get_metrics()
        
        assert metrics["total_events"] == 0
        assert metrics["search_events"] == 0
        assert metrics["click_events"] == 0
        assert metrics["search_v1"]["count"] == 0
        assert metrics["search_v2"]["count"] == 0
    
    def test_get_metrics_with_searches(self, manager):
        """Test metrics with search events."""
        manager.log_search("user1", "query", 10)
        manager.log_search("user2", "query", 15)
        
        metrics = manager.get_metrics()
        assert metrics["search_events"] == 2
        assert metrics["total_events"] == 2
    
    def test_get_metrics_ctr_calculation(self, manager):
        """Test click-through rate calculation."""
        # Log searches and clicks from multiple users to ensure variant is populated
        manager.split_ratio = 0.99  # Force v1 to ensure it gets populated
        
        for i in range(3):
            user_id = f"user_{i}"
            manager.assign_variant(user_id)
            manager.log_search(user_id, "shirts", 5)
            if i == 0:  # One click for CTR calculation
                manager.log_click(user_id, "prod1", position=0)
        
        metrics = manager.get_metrics()
        
        # v1 should have searches and clicks
        assert metrics["search_v1"]["count"] >= 1
        assert metrics["search_v1"]["clicks"] >= 1
    
    def test_avg_search_time(self, manager):
        """Test average search time calculation."""
        manager.log_search("user1", "query", 5, search_time_ms=100.0)
        manager.log_search("user2", "query", 10, search_time_ms=200.0)
        
        metrics = manager.get_metrics()
        assert metrics["avg_search_time_ms"] == 150.0
    
    def test_avg_results(self, manager):
        """Test average results calculation."""
        manager.log_search("user1", "query1", 10)
        manager.log_search("user2", "query2", 20)
        manager.log_search("user3", "query3", 30)
        
        metrics = manager.get_metrics()
        assert metrics["avg_results"] == 20.0


class TestEventFiltering:
    """Test event retrieval and filtering."""
    
    def test_get_events_by_user(self, manager):
        """Test filtering events by user."""
        manager.log_search("user1", "query", 5)
        manager.log_search("user2", "query", 10)
        manager.log_click("user1", "prod1")
        
        events = manager.get_events(user_id="user1")
        
        assert len(events) == 2
        assert all(e.user_id == "user1" for e in events)
    
    def test_get_events_by_type(self, manager):
        """Test filtering events by type."""
        manager.log_search("user1", "query", 5)
        manager.log_search("user2", "query", 10)
        manager.log_click("user1", "prod1")
        
        search_events = manager.get_events(event_type="search")
        click_events = manager.get_events(event_type="click")
        
        assert len(search_events) == 2
        assert len(click_events) == 1
    
    def test_get_events_limit(self, manager):
        """Test event limit."""
        for i in range(10):
            manager.log_search(f"user{i}", "query", 5)
        
        events = manager.get_events(limit=5)
        assert len(events) == 5
    
    def test_get_events_by_variant(self, manager):
        """Test filtering by variant."""
        manager.split_ratio = 0.99  # Force v1
        
        manager.log_search("user1", "query", 5)
        
        events = manager.get_events(variant=ExperimentVariant.SEARCH_V1)
        assert len(events) >= 1


class TestReset:
    """Test data reset functionality."""
    
    def test_reset_clears_assignments(self, manager, user_id):
        """Test that reset clears assignments."""
        manager.assign_variant(user_id)
        assert manager.get_assignment(user_id) is not None
        
        manager.reset()
        assert manager.get_assignment(user_id) is None
    
    def test_reset_clears_events(self, manager, user_id):
        """Test that reset clears events."""
        manager.log_search(user_id, "query", 5)
        assert len(manager.get_events()) > 0
        
        manager.reset()
        assert len(manager.get_events()) == 0


class TestGlobalInstance:
    """Test global experiment manager instance."""
    
    def test_get_experiment_manager_singleton(self):
        """Test that get_experiment_manager returns singleton."""
        reset_experiment_manager()
        
        manager1 = get_experiment_manager()
        manager2 = get_experiment_manager()
        
        assert manager1 is manager2
    
    def test_reset_experiment_manager(self):
        """Test reset of global instance."""
        reset_experiment_manager()
        manager1 = get_experiment_manager()
        manager1.assign_variant("user1")
        
        reset_experiment_manager()
        manager2 = get_experiment_manager()
        
        assert manager1 is not manager2
