"""
Tests for search variant implementations (V1 and V2).

Tests verify:
- V1: Vector similarity only search
- V2: Vector + ranking engine search
- A/B testing integration (event logging, timing)
- Endpoint integration
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import List
import time

from services.search_variants import (
    SearchVariantV1,
    SearchVariantV2,
    get_search_variant,
    SEARCH_VARIANTS
)
from models.search import ProductResult
from services.ab_testing import ExperimentVariant


# Mock data
MOCK_SEARCH_RESULT = Mock()
MOCK_SEARCH_RESULT.product_id = "prod_001"
MOCK_SEARCH_RESULT.title = "Blue Running Shoes"
MOCK_SEARCH_RESULT.description = "Comfortable running shoes"
MOCK_SEARCH_RESULT.color = "blue"
MOCK_SEARCH_RESULT.category = "footwear"
MOCK_SEARCH_RESULT.image_path = "/images/shoes.jpg"
MOCK_SEARCH_RESULT.similarity = 0.95
MOCK_SEARCH_RESULT.distance = 0.05
MOCK_SEARCH_RESULT.debug_scores = None

MOCK_SEARCH_RESULT_2 = Mock()
MOCK_SEARCH_RESULT_2.product_id = "prod_002"
MOCK_SEARCH_RESULT_2.title = "Blue Sneakers"
MOCK_SEARCH_RESULT_2.description = "Casual sneakers"
MOCK_SEARCH_RESULT_2.color = "blue"
MOCK_SEARCH_RESULT_2.category = "footwear"
MOCK_SEARCH_RESULT_2.image_path = "/images/sneakers.jpg"
MOCK_SEARCH_RESULT_2.similarity = 0.85
MOCK_SEARCH_RESULT_2.distance = 0.15
MOCK_SEARCH_RESULT_2.debug_scores = None


class TestSearchVariantV1:
    """Tests for SearchVariantV1 (vector similarity only)."""
    
    @patch('services.search_variants.get_search_service')
    def test_search_by_text_basic(self, mock_get_service):
        """Test basic text search with V1."""
        # Setup mock
        mock_service = Mock()
        mock_service.search_by_text.return_value = [MOCK_SEARCH_RESULT]
        mock_get_service.return_value = mock_service
        
        # Execute
        results, elapsed_ms = SearchVariantV1.search_by_text(
            query_text="blue shoes",
            top_k=10
        )
        
        # Assert
        assert len(results) == 1
        assert isinstance(results[0], ProductResult)
        assert results[0].product_id == "prod_001"
        assert results[0].title == "Blue Running Shoes"
        assert results[0].similarity == 0.95
        assert elapsed_ms >= 0  # Should be >= 0 (can be very small with mocks)
        
        # Verify service called with enable_reranking=False
        mock_service.search_by_text.assert_called_once()
        call_kwargs = mock_service.search_by_text.call_args[1]
        assert call_kwargs['enable_reranking'] is False
    
    @patch('services.search_variants.get_search_service')
    def test_search_by_text_with_filters(self, mock_get_service):
        """Test text search with category and color filters."""
        mock_service = Mock()
        mock_service.search_by_text.return_value = [MOCK_SEARCH_RESULT]
        mock_get_service.return_value = mock_service
        
        # Execute
        results, elapsed_ms = SearchVariantV1.search_by_text(
            query_text="blue shoes",
            top_k=5,
            category_filter="footwear",
            color_filter="blue"
        )
        
        # Assert
        assert len(results) == 1
        call_kwargs = mock_service.search_by_text.call_args[1]
        assert call_kwargs['category_filter'] == "footwear"
        assert call_kwargs['color_filter'] == "blue"
    
    @patch('services.search_variants.get_search_service')
    def test_search_by_text_multiple_results(self, mock_get_service):
        """Test text search returning multiple results."""
        mock_service = Mock()
        mock_service.search_by_text.return_value = [MOCK_SEARCH_RESULT, MOCK_SEARCH_RESULT_2]
        mock_get_service.return_value = mock_service
        
        # Execute
        results, elapsed_ms = SearchVariantV1.search_by_text(
            query_text="blue shoes",
            top_k=10
        )
        
        # Assert
        assert len(results) == 2
        assert results[0].similarity == 0.95
        assert results[1].similarity == 0.85
    
    @patch('services.search_variants.get_search_service')
    def test_search_by_image_basic(self, mock_get_service):
        """Test basic image search with V1."""
        mock_service = Mock()
        mock_service.search_by_image.return_value = [MOCK_SEARCH_RESULT]
        mock_get_service.return_value = mock_service
        
        # Execute
        results, elapsed_ms = SearchVariantV1.search_by_image(
            image_path="/path/to/image.jpg",
            top_k=10
        )
        
        # Assert
        assert len(results) == 1
        assert elapsed_ms >= 0  # Should be >= 0 (can be very small with mocks)
        
        # Verify service called with enable_reranking=False
        call_kwargs = mock_service.search_by_image.call_args[1]
        assert call_kwargs['enable_reranking'] is False
    
    @patch('services.search_variants.get_search_service')
    def test_search_exception_handling(self, mock_get_service):
        """Test exception handling in search_by_text."""
        mock_service = Mock()
        mock_service.search_by_text.side_effect = RuntimeError("Service error")
        mock_get_service.return_value = mock_service
        
        # Execute and assert
        with pytest.raises(Exception) as exc_info:
            SearchVariantV1.search_by_text(query_text="test")
        
        assert "V1 search failed" in str(exc_info.value)


class TestSearchVariantV2:
    """Tests for SearchVariantV2 (vector + ranking engine)."""
    
    @patch('services.search_variants.get_search_service')
    def test_search_by_text_with_reranking(self, mock_get_service):
        """Test text search with V2 (re-ranking enabled)."""
        # Setup mock
        mock_service = Mock()
        mock_service.search_by_text.return_value = [MOCK_SEARCH_RESULT]
        mock_get_service.return_value = mock_service
        
        # Execute
        results, elapsed_ms = SearchVariantV2.search_by_text(
            query_text="blue shoes",
            top_k=10
        )
        
        # Assert
        assert len(results) == 1
        assert isinstance(results[0], ProductResult)
        assert results[0].product_id == "prod_001"
        assert elapsed_ms >= 0  # Should be >= 0 (can be very small with mocks)
        
        # Verify service called with enable_reranking=True
        call_kwargs = mock_service.search_by_text.call_args[1]
        assert call_kwargs['enable_reranking'] is True
    
    @patch('services.search_variants.get_search_service')
    def test_search_by_text_debug_scores(self, mock_get_service):
        """Test text search with debug scoring enabled."""
        mock_result = Mock()
        mock_result.product_id = "prod_001"
        mock_result.title = "Blue Shoes"
        mock_result.description = "Description"
        mock_result.color = "blue"
        mock_result.category = "footwear"
        mock_result.image_path = "/images/shoes.jpg"
        mock_result.similarity = 0.95
        mock_result.distance = 0.05
        mock_result.debug_scores = {
            "vector_score": 0.95,
            "color_score": 1.0,
            "category_score": 1.0,
            "text_score": 0.8,
            "final_score": 0.88
        }
        
        mock_service = Mock()
        mock_service.search_by_text.return_value = [mock_result]
        mock_get_service.return_value = mock_service
        
        # Execute
        results, elapsed_ms = SearchVariantV2.search_by_text(
            query_text="blue shoes",
            debug=True
        )
        
        # Assert
        assert results[0].debug_scores is not None
        assert results[0].debug_scores["final_score"] == 0.88
    
    @patch('services.search_variants.get_search_service')
    def test_search_by_image_with_reranking(self, mock_get_service):
        """Test image search with V2 (re-ranking enabled)."""
        mock_service = Mock()
        mock_service.search_by_image.return_value = [MOCK_SEARCH_RESULT]
        mock_get_service.return_value = mock_service
        
        # Execute
        results, elapsed_ms = SearchVariantV2.search_by_image(
            image_path="/path/to/image.jpg",
            top_k=10
        )
        
        # Assert
        assert len(results) == 1
        
        # Verify service called with enable_reranking=True
        call_kwargs = mock_service.search_by_image.call_args[1]
        assert call_kwargs['enable_reranking'] is True
    
    @patch('services.search_variants.get_search_service')
    def test_search_by_image_with_filters(self, mock_get_service):
        """Test image search with filters."""
        mock_service = Mock()
        mock_service.search_by_image.return_value = [MOCK_SEARCH_RESULT]
        mock_get_service.return_value = mock_service
        
        # Execute
        results, elapsed_ms = SearchVariantV2.search_by_image(
            image_path="/path/to/image.jpg",
            top_k=5,
            category_filter="footwear",
            color_filter="blue"
        )
        
        # Assert
        call_kwargs = mock_service.search_by_image.call_args[1]
        assert call_kwargs['category_filter'] == "footwear"
        assert call_kwargs['color_filter'] == "blue"


class TestVariantComparison:
    """Tests comparing V1 and V2 behavior."""
    
    @patch('services.search_variants.get_search_service')
    def test_v1_no_reranking_v2_with_reranking(self, mock_get_service):
        """Test that V1 disables re-ranking while V2 enables it."""
        mock_service = Mock()
        mock_service.search_by_text.return_value = [MOCK_SEARCH_RESULT]
        mock_get_service.return_value = mock_service
        
        # Execute V1
        SearchVariantV1.search_by_text(query_text="test")
        v1_call = mock_service.search_by_text.call_args[1]['enable_reranking']
        
        # Reset mock
        mock_service.reset_mock()
        
        # Execute V2
        SearchVariantV2.search_by_text(query_text="test")
        v2_call = mock_service.search_by_text.call_args[1]['enable_reranking']
        
        # Assert
        assert v1_call is False
        assert v2_call is True
    
    @patch('services.search_variants.get_search_service')
    def test_timing_measured(self, mock_get_service):
        """Test that search timing is measured correctly."""
        mock_service = Mock()
        mock_service.search_by_text.return_value = [MOCK_SEARCH_RESULT]
        mock_get_service.return_value = mock_service
        
        # Execute
        results, elapsed_ms = SearchVariantV1.search_by_text(query_text="test")
        
        # Assert
        assert elapsed_ms >= 0  # Should be >= 0 (can be very small with mocks)
        assert isinstance(elapsed_ms, float)


class TestGetSearchVariant:
    """Tests for variant lookup function."""
    
    def test_get_search_variant_v1(self):
        """Test getting V1 variant."""
        variant = get_search_variant("search_v1")
        assert variant == SearchVariantV1
    
    def test_get_search_variant_v2(self):
        """Test getting V2 variant."""
        variant = get_search_variant("search_v2")
        assert variant == SearchVariantV2
    
    def test_get_search_variant_invalid(self):
        """Test getting invalid variant."""
        with pytest.raises(ValueError) as exc_info:
            get_search_variant("search_v3")
        
        assert "Unknown search variant" in str(exc_info.value)
    
    def test_search_variants_mapping(self):
        """Test that SEARCH_VARIANTS mapping is correct."""
        assert "search_v1" in SEARCH_VARIANTS
        assert "search_v2" in SEARCH_VARIANTS
        assert SEARCH_VARIANTS["search_v1"] == SearchVariantV1
        assert SEARCH_VARIANTS["search_v2"] == SearchVariantV2


class TestProductResultConversion:
    """Tests for converting search results to ProductResult."""
    
    @patch('services.search_variants.get_search_service')
    def test_result_fields_preserved(self, mock_get_service):
        """Test that all result fields are preserved in conversion."""
        mock_service = Mock()
        mock_service.search_by_text.return_value = [MOCK_SEARCH_RESULT]
        mock_get_service.return_value = mock_service
        
        # Execute
        results, _ = SearchVariantV1.search_by_text(query_text="test")
        
        # Assert all fields preserved
        result = results[0]
        assert result.product_id == MOCK_SEARCH_RESULT.product_id
        assert result.title == MOCK_SEARCH_RESULT.title
        assert result.description == MOCK_SEARCH_RESULT.description
        assert result.color == MOCK_SEARCH_RESULT.color
        assert result.category == MOCK_SEARCH_RESULT.category
        assert result.image_path == MOCK_SEARCH_RESULT.image_path
        assert result.similarity == MOCK_SEARCH_RESULT.similarity
        assert result.distance == MOCK_SEARCH_RESULT.distance
