"""
Integration tests for A/B testing with search variants.

Tests verify:
- Variant assignment and consistency
- Search event logging
- A/B framework integration
"""
import pytest
from unittest.mock import Mock, patch
from services.ab_testing import (
    get_experiment_manager,
    reset_experiment_manager,
    ExperimentVariant,
    SearchEvent,
)
from services.search_variants import (
    SearchVariantV1,
    SearchVariantV2,
    get_search_variant,
)
from models.search import ProductResult


@pytest.fixture
def cleanup_ab():
    """Cleanup A/B testing data before and after tests."""
    reset_experiment_manager()
    yield
    reset_experiment_manager()


class TestSearchVariantsDirect:
    """Direct tests for search variants."""
    
    @patch('services.search_variants.get_search_service')
    def test_v1_returns_results(self, mock_get_service, cleanup_ab):
        """Test that V1 search returns results."""
        mock_result = Mock()
        mock_result.product_id = "prod_001"
        mock_result.title = "Blue Shoes"
        mock_result.description = "Running shoes"
        mock_result.color = "blue"
        mock_result.category = "footwear"
        mock_result.image_path = "/img.jpg"
        mock_result.similarity = 0.95
        mock_result.distance = 0.05
        mock_result.debug_scores = None
        
        mock_service = Mock()
        mock_service.search_by_text.return_value = [mock_result]
        mock_get_service.return_value = mock_service
        
        results, elapsed = SearchVariantV1.search_by_text("test")
        
        assert len(results) == 1
        assert isinstance(results[0], ProductResult)
        assert results[0].product_id == "prod_001"
        assert results[0].title == "Blue Shoes"
    
    @patch('services.search_variants.get_search_service')
    def test_v2_returns_results(self, mock_get_service, cleanup_ab):
        """Test that V2 search returns results."""
        mock_result = Mock()
        mock_result.product_id = "prod_002"
        mock_result.title = "Red Shoes"
        mock_result.description = "Casual shoes"
        mock_result.color = "red"
        mock_result.category = "footwear"
        mock_result.image_path = "/img2.jpg"
        mock_result.similarity = 0.88
        mock_result.distance = 0.12
        mock_result.debug_scores = None
        
        mock_service = Mock()
        mock_service.search_by_text.return_value = [mock_result]
        mock_get_service.return_value = mock_service
        
        results, elapsed = SearchVariantV2.search_by_text("test")
        
        assert len(results) == 1
        assert results[0].product_id == "prod_002"
        assert results[0].title == "Red Shoes"
    
    @patch('services.search_variants.get_search_service')
    def test_v1_disables_reranking(self, mock_get_service, cleanup_ab):
        """Test that V1 disables re-ranking."""
        mock_service = Mock()
        mock_service.search_by_text.return_value = []
        mock_get_service.return_value = mock_service
        
        SearchVariantV1.search_by_text("test")
        
        # Check that enable_reranking=False was passed
        call_kwargs = mock_service.search_by_text.call_args[1]
        assert call_kwargs['enable_reranking'] is False
    
    @patch('services.search_variants.get_search_service')
    def test_v2_enables_reranking(self, mock_get_service, cleanup_ab):
        """Test that V2 enables re-ranking."""
        mock_service = Mock()
        mock_service.search_by_text.return_value = []
        mock_get_service.return_value = mock_service
        
        SearchVariantV2.search_by_text("test")
        
        # Check that enable_reranking=True was passed
        call_kwargs = mock_service.search_by_text.call_args[1]
        assert call_kwargs['enable_reranking'] is True
    
    @patch('services.search_variants.get_search_service')
    def test_v1_image_search(self, mock_get_service, cleanup_ab):
        """Test V1 image search."""
        mock_result = Mock()
        mock_result.product_id = "prod_001"
        mock_result.title = "Blue Shoes"
        mock_result.description = "Running shoes"
        mock_result.color = "blue"
        mock_result.category = "footwear"
        mock_result.image_path = "/img.jpg"
        mock_result.similarity = 0.95
        mock_result.distance = 0.05
        mock_result.debug_scores = None
        
        mock_service = Mock()
        mock_service.search_by_image.return_value = [mock_result]
        mock_get_service.return_value = mock_service
        
        results, elapsed = SearchVariantV1.search_by_image("/path/to/img.jpg")
        
        assert len(results) == 1
        # Check that enable_reranking=False was passed
        call_kwargs = mock_service.search_by_image.call_args[1]
        assert call_kwargs['enable_reranking'] is False
    
    @patch('services.search_variants.get_search_service')
    def test_v2_image_search(self, mock_get_service, cleanup_ab):
        """Test V2 image search."""
        mock_result = Mock()
        mock_result.product_id = "prod_002"
        mock_result.title = "Red Shoes"
        mock_result.description = "Casual shoes"
        mock_result.color = "red"
        mock_result.category = "footwear"
        mock_result.image_path = "/img2.jpg"
        mock_result.similarity = 0.88
        mock_result.distance = 0.12
        mock_result.debug_scores = None
        
        mock_service = Mock()
        mock_service.search_by_image.return_value = [mock_result]
        mock_get_service.return_value = mock_service
        
        results, elapsed = SearchVariantV2.search_by_image("/path/to/img.jpg")
        
        assert len(results) == 1
        # Check that enable_reranking=True was passed
        call_kwargs = mock_service.search_by_image.call_args[1]
        assert call_kwargs['enable_reranking'] is True


class TestABFrameworkIntegration:
    """Tests for A/B framework integration with search variants."""
    
    def test_get_search_variant_v1(self, cleanup_ab):
        """Test getting V1 search variant."""
        variant = get_search_variant("search_v1")
        assert variant == SearchVariantV1
    
    def test_get_search_variant_v2(self, cleanup_ab):
        """Test getting V2 search variant."""
        variant = get_search_variant("search_v2")
        assert variant == SearchVariantV2
    
    def test_get_invalid_variant(self, cleanup_ab):
        """Test getting invalid variant raises error."""
        with pytest.raises(ValueError) as exc:
            get_search_variant("search_v999")
        assert "Unknown search variant" in str(exc.value)
    
    def test_ab_framework_assignment(self, cleanup_ab):
        """Test that A/B framework assigns variants correctly."""
        manager = get_experiment_manager()
        
        # Assign variant to user1
        assignment1 = manager.assign_variant("user1")
        
        # Assign variant to user2
        assignment2 = manager.assign_variant("user2")
        
        # Both should have valid assignments
        assert assignment1 is not None
        assert assignment2 is not None
        assert assignment1.user_id == "user1"
        assert assignment2.user_id == "user2"
        assert assignment1.variant in [ExperimentVariant.SEARCH_V1, ExperimentVariant.SEARCH_V2]
        assert assignment2.variant in [ExperimentVariant.SEARCH_V1, ExperimentVariant.SEARCH_V2]
    
    def test_search_event_logging(self, cleanup_ab):
        """Test that search events are logged correctly."""
        manager = get_experiment_manager()
        
        # Log search event
        manager.log_search(
            user_id="user1",
            query="test query",
            results_count=5,
            search_time_ms=42.5
        )
        
        # Verify event was logged
        events = manager.get_events(user_id="user1")
        assert len(events) == 1
        assert isinstance(events[0], SearchEvent)
        assert events[0].user_id == "user1"
        assert events[0].query == "test query"
        assert events[0].results_count == 5
        assert events[0].search_time_ms == 42.5
    
    def test_variant_consistency(self, cleanup_ab):
        """Test that variant assignment is consistent for same user."""
        manager = get_experiment_manager()
        
        # First assignment
        assignment1 = manager.assign_variant("user123")
        variant1 = assignment1.variant
        
        # Second assignment (should get same variant)
        assignment2 = manager.get_assignment("user123")
        variant2 = assignment2.variant
        
        # Should be identical
        assert variant1 == variant2
    
    def test_variant_distribution(self, cleanup_ab):
        """Test that variants are distributed to different users."""
        manager = get_experiment_manager()
        
        # Assign to many users
        v1_count = 0
        v2_count = 0
        for i in range(100):
            assignment = manager.assign_variant(f"user{i}")
            if assignment.variant == ExperimentVariant.SEARCH_V1:
                v1_count += 1
            else:
                v2_count += 1
        
        # Both variants should have been assigned
        assert v1_count > 0
        assert v2_count > 0
        # Should be roughly balanced (50/50)
        assert abs(v1_count - v2_count) < 50  # Allow up to 50 difference
    
    @patch('services.search_variants.get_search_service')
    def test_end_to_end_v1_search_with_logging(self, mock_get_service, cleanup_ab):
        """End-to-end test: Assign V1, execute search, log event."""
        # Setup mock
        mock_result = Mock()
        mock_result.product_id = "prod_001"
        mock_result.title = "Test Product"
        mock_result.description = "Description"
        mock_result.color = "blue"
        mock_result.category = "test"
        mock_result.image_path = "/img.jpg"
        mock_result.similarity = 0.9
        mock_result.distance = 0.1
        mock_result.debug_scores = None
        
        mock_service = Mock()
        mock_service.search_by_text.return_value = [mock_result]
        mock_get_service.return_value = mock_service
        
        manager = get_experiment_manager()
        
        # 1. Assign variant
        assignment = manager.assign_variant("user_test")
        assert assignment.variant in [ExperimentVariant.SEARCH_V1, ExperimentVariant.SEARCH_V2]
        
        # 2. Execute search
        variant = get_search_variant("search_v1")
        results, elapsed_ms = variant.search_by_text("test query")
        
        # 3. Log event
        manager.log_search(
            user_id="user_test",
            query="test query",
            results_count=len(results),
            search_time_ms=elapsed_ms
        )
        
        # 4. Verify everything
        assert len(results) == 1
        events = manager.get_events(user_id="user_test")
        assert len(events) == 1
        assert events[0].query == "test query"
        assert events[0].results_count == 1
    
    @patch('services.search_variants.get_search_service')
    def test_end_to_end_v2_search_with_logging(self, mock_get_service, cleanup_ab):
        """End-to-end test: Assign V2, execute search, log event."""
        # Setup mock
        mock_result = Mock()
        mock_result.product_id = "prod_002"
        mock_result.title = "Another Product"
        mock_result.description = "Description 2"
        mock_result.color = "red"
        mock_result.category = "test"
        mock_result.image_path = "/img2.jpg"
        mock_result.similarity = 0.85
        mock_result.distance = 0.15
        mock_result.debug_scores = None
        
        mock_service = Mock()
        mock_service.search_by_text.return_value = [mock_result]
        mock_get_service.return_value = mock_service
        
        manager = get_experiment_manager()
        
        # 1. Assign variant
        assignment = manager.assign_variant("user_test2")
        assert assignment.variant in [ExperimentVariant.SEARCH_V1, ExperimentVariant.SEARCH_V2]
        
        # 2. Execute search
        variant = get_search_variant("search_v2")
        results, elapsed_ms = variant.search_by_text("test query 2")
        
        # 3. Log event
        manager.log_search(
            user_id="user_test2",
            query="test query 2",
            results_count=len(results),
            search_time_ms=elapsed_ms
        )
        
        # 4. Verify everything
        assert len(results) == 1
        events = manager.get_events(user_id="user_test2")
        assert len(events) == 1
        assert events[0].query == "test query 2"
        assert events[0].results_count == 1
