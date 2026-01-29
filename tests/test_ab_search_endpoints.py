"""
Integration tests for A/B testing search endpoints.

Tests verify:
- Variant assignment and injection
- Search execution and event logging
- Response structure and headers
- Error handling and validation
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import json

from services.ab_testing import get_experiment_manager, reset_experiment_manager, ExperimentVariant, SearchEvent
from services.search_variants import SearchVariantV1, SearchVariantV2, get_search_variant
from models.search import ProductResult


@pytest.fixture
def cleanup_ab():
    """Cleanup A/B testing data before and after tests."""
    reset_experiment_manager()
    yield
    reset_experiment_manager()


class TestSearchVariantsDirectly:
    """Direct tests for search variants without endpoint dependencies."""
    
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
    """Tests for /search-ab/text endpoint."""
    
    @patch('api.ab_search.get_search_variant')
    def test_text_search_success(self, mock_get_variant, client, cleanup_ab):
        """Test successful text search with A/B variant."""
        # Mock search variant
        mock_variant = Mock()
        mock_variant.search_by_text.return_value = (
            [
                Mock(
                    product_id="prod_001",
                    title="Blue Shoes",
                    description="Running shoes",
                    color="blue",
                    category="footwear",
                    image_path="/img.jpg",
                    similarity=0.95,
                    distance=0.05,
                    debug_scores=None
                )
            ],
            45.2  # elapsed_ms
        )
        mock_get_variant.return_value = mock_variant
        
        # Execute
        response = client.post(
            "/search-ab/text?query=blue%20shoes&top_k=5",
            headers={"X-User-ID": "user123"}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "blue shoes"
        assert len(data["results"]) == 1
        assert data["results"][0]["product_id"] == "prod_001"
        assert data["total_results"] == 1
    
    @patch('api.ab_search.get_search_variant')
    def test_text_search_event_logged(self, mock_get_variant, client, cleanup_ab):
        """Test that search event is logged to A/B framework."""
        mock_variant = Mock()
        mock_variant.search_by_text.return_value = ([], 10.0)
        mock_get_variant.return_value = mock_variant
        
        # Execute
        response = client.post(
            "/search-ab/text?query=test&top_k=10",
            headers={"X-User-ID": "user123"}
        )
        
        # Assert
        assert response.status_code == 200
        
        # Verify event was logged
        manager = get_experiment_manager()
        events = manager.get_events(user_id="user123")
        assert len(events) == 1
        assert events[0]["event_type"] == "search"
        assert "test" in events[0]["query"]
        assert events[0]["results_count"] == 0
    
    @patch('api.ab_search.get_search_variant')
    def test_text_search_with_filters(self, mock_get_variant, client, cleanup_ab):
        """Test text search with category and color filters."""
        mock_variant = Mock()
        mock_variant.search_by_text.return_value = ([], 10.0)
        mock_get_variant.return_value = mock_variant
        
        # Execute
        response = client.post(
            "/search-ab/text?query=shoes&category=footwear&color=blue&top_k=5",
            headers={"X-User-ID": "user123"}
        )
        
        # Assert
        assert response.status_code == 200
        
        # Verify variant called with filters
        call_kwargs = mock_variant.search_by_text.call_args[1]
        assert call_kwargs['category_filter'] == "footwear"
        assert call_kwargs['color_filter'] == "blue"
    
    @patch('api.ab_search.get_search_variant')
    def test_text_search_missing_query(self, mock_get_variant, client, cleanup_ab):
        """Test text search without required query parameter."""
        # Execute
        response = client.post(
            "/search-ab/text",
            headers={"X-User-ID": "user123"}
        )
        
        # Assert - should fail validation
        assert response.status_code == 422  # Unprocessable Entity
    
    @patch('api.ab_search.get_search_variant')
    def test_text_search_variant_assignment(self, mock_get_variant, client, cleanup_ab):
        """Test that variant is correctly assigned to user."""
        mock_variant = Mock()
        mock_variant.search_by_text.return_value = ([], 10.0)
        mock_get_variant.return_value = mock_variant
        
        # Execute first search (triggers assignment)
        response1 = client.post(
            "/search-ab/text?query=test1",
            headers={"X-User-ID": "user123"}
        )
        
        # Execute second search (should get same variant)
        response2 = client.post(
            "/search-ab/text?query=test2",
            headers={"X-User-ID": "user123"}
        )
        
        # Assert both calls succeeded
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verify user has consistent assignment
        manager = get_experiment_manager()
        assignment = manager.get_assignment("user123")
        assert assignment is not None
        assert assignment.variant in [ExperimentVariant.SEARCH_V1, ExperimentVariant.SEARCH_V2]


class TestABSearchImageEndpoint:
    """Tests for /search-ab/image endpoint."""
    
    @patch('api.ab_search.get_search_variant')
    def test_image_search_success(self, mock_get_variant, client, cleanup_ab):
        """Test successful image search with A/B variant."""
        # Mock search variant
        mock_variant = Mock()
        mock_variant.search_by_image.return_value = (
            [
                Mock(
                    product_id="prod_001",
                    title="Blue Shoes",
                    description="Running shoes",
                    color="blue",
                    category="footwear",
                    image_path="/img.jpg",
                    similarity=0.95,
                    distance=0.05,
                    debug_scores=None
                )
            ],
            52.1  # elapsed_ms
        )
        mock_get_variant.return_value = mock_variant
        
        # Execute
        response = client.post(
            "/search-ab/image?top_k=5",
            files={"file": ("test.jpg", b"fake_image_data", "image/jpeg")},
            headers={"X-User-ID": "user456"}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "test.jpg"
        assert len(data["results"]) == 1
        assert data["total_results"] == 1
    
    @patch('api.ab_search.get_search_variant')
    def test_image_search_event_logged(self, mock_get_variant, client, cleanup_ab):
        """Test that image search event is logged."""
        mock_variant = Mock()
        mock_variant.search_by_image.return_value = ([], 20.0)
        mock_get_variant.return_value = mock_variant
        
        # Execute
        response = client.post(
            "/search-ab/image?top_k=5",
            files={"file": ("test.jpg", b"fake_image_data", "image/jpeg")},
            headers={"X-User-ID": "user456"}
        )
        
        # Assert
        assert response.status_code == 200
        
        # Verify event was logged
        manager = get_experiment_manager()
        events = manager.get_events(user_id="user456")
        assert len(events) == 1
        assert events[0]["event_type"] == "search"
        assert "[image:" in events[0]["query"]
        assert "test.jpg" in events[0]["query"]
    
    @patch('api.ab_search.get_search_variant')
    def test_image_search_invalid_file(self, mock_get_variant, client, cleanup_ab):
        """Test image search with invalid file type."""
        # Execute with non-image file
        response = client.post(
            "/search-ab/image?top_k=5",
            files={"file": ("test.txt", b"not_an_image", "text/plain")},
            headers={"X-User-ID": "user456"}
        )
        
        # Assert
        assert response.status_code == 400
        assert "image" in response.json()["detail"].lower()
    
    @patch('api.ab_search.get_search_variant')
    def test_image_search_missing_file(self, mock_get_variant, client, cleanup_ab):
        """Test image search without file."""
        # Execute without file
        response = client.post(
            "/search-ab/image?top_k=5",
            headers={"X-User-ID": "user456"}
        )
        
        # Assert
        assert response.status_code == 422  # Validation error


class TestABSearchVariantsEndpoint:
    """Tests for /search-ab/variants endpoint."""
    
    def test_get_available_variants(self, client):
        """Test getting list of available variants."""
        # Execute
        response = client.get("/search-ab/variants")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "variants" in data
        assert len(data["variants"]) == 2
        
        variant_names = [v["name"] for v in data["variants"]]
        assert "search_v1" in variant_names
        assert "search_v2" in variant_names
    
    def test_variants_have_descriptions(self, client):
        """Test that variants have descriptions."""
        # Execute
        response = client.get("/search-ab/variants")
        
        # Assert
        data = response.json()
        for variant in data["variants"]:
            assert "name" in variant
            assert "description" in variant
            assert variant["description"]  # Not empty


class TestABSearchVariantInfoEndpoint:
    """Tests for /search-ab/variant-info/{variant_name} endpoint."""
    
    def test_variant_info_v1(self, client):
        """Test getting info for search_v1."""
        # Execute
        response = client.get("/search-ab/variant-info/search_v1")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "search_v1"
        assert data["type"] == "baseline"
        assert "vector_similarity" in data["scoring_factors"]
        assert data["reranking_enabled"] is False
    
    def test_variant_info_v2(self, client):
        """Test getting info for search_v2."""
        # Execute
        response = client.get("/search-ab/variant-info/search_v2")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "search_v2"
        assert data["type"] == "enhanced"
        assert "vector_similarity" in data["scoring_factors"]
        assert "color_match" in data["scoring_factors"]
        assert "category_match" in data["scoring_factors"]
        assert "text_similarity" in data["scoring_factors"]
        assert data["reranking_enabled"] is True
    
    def test_variant_info_invalid(self, client):
        """Test getting info for invalid variant."""
        # Execute
        response = client.get("/search-ab/variant-info/search_v3")
        
        # Assert
        assert response.status_code == 404
        assert "Unknown variant" in response.json()["detail"]


class TestABSearchErrorHandling:
    """Tests for error handling in A/B search endpoints."""
    
    @patch('api.ab_search.get_search_variant')
    def test_search_service_error(self, mock_get_variant, client, cleanup_ab):
        """Test handling of search service errors."""
        mock_variant = Mock()
        mock_variant.search_by_text.side_effect = RuntimeError("Service error")
        mock_get_variant.return_value = mock_variant
        
        # Execute
        response = client.post(
            "/search-ab/text?query=test",
            headers={"X-User-ID": "user123"}
        )
        
        # Assert
        assert response.status_code == 500
        assert "failed" in response.json()["detail"].lower()
    
    @patch('api.ab_search.get_search_variant')
    def test_invalid_top_k(self, mock_get_variant, client, cleanup_ab):
        """Test validation of top_k parameter."""
        # Execute with top_k > 100
        response = client.post(
            "/search-ab/text?query=test&top_k=150",
            headers={"X-User-ID": "user123"}
        )
        
        # Assert
        assert response.status_code == 422  # Validation error
    
    @patch('api.ab_search.get_search_variant')
    def test_zero_top_k(self, mock_get_variant, client, cleanup_ab):
        """Test validation that top_k must be >= 1."""
        # Execute with top_k = 0
        response = client.post(
            "/search-ab/text?query=test&top_k=0",
            headers={"X-User-ID": "user123"}
        )
        
        # Assert
        assert response.status_code == 422  # Validation error


class TestABSearchMetrics:
    """Tests for metrics related to A/B search."""
    
    @patch('api.ab_search.get_search_variant')
    def test_search_timing_captured(self, mock_get_variant, client, cleanup_ab):
        """Test that search timing is captured in events."""
        mock_variant = Mock()
        mock_variant.search_by_text.return_value = ([], 42.5)  # 42.5ms
        mock_get_variant.return_value = mock_variant
        
        # Execute
        response = client.post(
            "/search-ab/text?query=test",
            headers={"X-User-ID": "user123"}
        )
        
        # Assert
        assert response.status_code == 200
        
        # Verify timing in event
        manager = get_experiment_manager()
        events = manager.get_events(user_id="user123")
        assert len(events) == 1
        assert events[0]["search_time_ms"] is not None
    
    @patch('api.ab_search.get_search_variant')
    def test_results_count_captured(self, mock_get_variant, client, cleanup_ab):
        """Test that result count is captured in events."""
        mock_variant = Mock()
        results = [Mock() for _ in range(5)]
        mock_variant.search_by_text.return_value = (results, 10.0)
        mock_get_variant.return_value = mock_variant
        
        # Execute
        response = client.post(
            "/search-ab/text?query=test&top_k=5",
            headers={"X-User-ID": "user123"}
        )
        
        # Assert
        assert response.status_code == 200
        
        # Verify result count in event
        manager = get_experiment_manager()
        events = manager.get_events(user_id="user123")
        assert events[0]["results_count"] == 5
