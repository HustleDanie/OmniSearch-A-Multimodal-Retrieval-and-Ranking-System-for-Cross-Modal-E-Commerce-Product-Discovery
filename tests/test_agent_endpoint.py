"""
Tests for PersonalShopperAgent API endpoint.
"""
import pytest
import json
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def dummy_search_results():
    """Generate dummy search results for testing."""
    return [
        {
            "product_id": "PROD-001",
            "title": "Blue Casual Shirt",
            "description": "Comfortable cotton shirt",
            "color": "blue",
            "category": "apparel",
            "image_path": "/images/products/shirt-001.jpg",
            "similarity": 0.95,
            "distance": 0.05,
        },
        {
            "product_id": "PROD-002",
            "title": "Black Formal Blazer",
            "description": "Sharp tailored blazer",
            "color": "black",
            "category": "apparel",
            "image_path": "/images/products/blazer-001.jpg",
            "similarity": 0.90,
            "distance": 0.10,
        },
        {
            "product_id": "PROD-003",
            "title": "Navy Chinos",
            "description": "Versatile casual pants",
            "color": "navy",
            "category": "apparel",
            "image_path": "/images/products/chinos-001.jpg",
            "similarity": 0.88,
            "distance": 0.12,
        },
    ]


def dummy_llm_response():
    """Generate a mock LLM response."""
    return json.dumps({
        "recommendations": [
            {
                "title": "Blue Casual Shirt",
                "why": "Matches your preference for casual blue apparel and comfortable materials",
                "is_wildcard": False
            },
            {
                "title": "Black Formal Blazer",
                "why": "Complements your style with a professional piece",
                "is_wildcard": False
            },
            {
                "title": "Navy Chinos",
                "why": "Versatile neutral piece that works with multiple outfits",
                "is_wildcard": False
            },
            {
                "title": "Vintage Denim Jacket",
                "why": "A wildcard piece that adds character and edge",
                "is_wildcard": True
            }
        ]
    })


@patch("services.personal_shopper_agent.retrieve_context")
@patch("api.agent.get_llm_client")
@patch("api.agent.get_search_service")
def test_recommend_with_text_query(mock_search, mock_llm, mock_context):
    """Test recommendations with text query."""
    # Mock search service
    mock_search_instance = MagicMock()
    mock_search_instance.search_multimodal.return_value = [
        MagicMock(**result) for result in dummy_search_results()
    ]
    mock_search.return_value = mock_search_instance
    
    # Mock context retriever
    mock_context.return_value = "Mocked user preferences and search results"
    
    # Mock LLM client
    mock_llm_instance = MagicMock()
    mock_llm_instance.generate.return_value = dummy_llm_response()
    mock_llm.return_value = mock_llm_instance
    
    # Send request
    response = client.post(
        "/agent/recommend",
        data={
            "user_id": "user123",
            "query": "blue casual shirt",
            "top_k": 3,
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["user_id"] == "user123"
    assert data["query"] == "blue casual shirt"
    assert len(data["recommendations"]) == 4
    assert data["search_results_count"] == 3
    
    # Check first recommendation
    rec = data["recommendations"][0]
    assert rec["rank"] == 1
    assert rec["title"] == "Blue Casual Shirt"
    assert rec["is_wildcard"] is False
    assert rec["product_link"] is not None
    
    # Check wildcard recommendation (last)
    wildcard = data["recommendations"][3]
    assert wildcard["is_wildcard"] is True


@patch("api.agent.get_llm_client")
@patch("api.agent.get_search_service")
def test_recommend_missing_inputs(mock_search, mock_llm):
    """Test that endpoint rejects missing query and image."""
    response = client.post(
        "/agent/recommend",
        data={
            "user_id": "user123",
        }
    )
    
    assert response.status_code == 400
    assert "at least one of" in response.json()["detail"].lower()


@patch("api.agent.get_llm_client")
@patch("api.agent.get_search_service")
def test_recommend_without_llm_client(mock_search, mock_llm):
    """Test error handling when LLM client is not configured."""
    # Mock search service
    mock_search_instance = MagicMock()
    mock_search_instance.search_multimodal.return_value = [
        MagicMock(**result) for result in dummy_search_results()
    ]
    mock_search.return_value = mock_search_instance
    
    # Mock LLM client as None
    mock_llm.return_value = None
    
    response = client.post(
        "/agent/recommend",
        data={
            "user_id": "user123",
            "query": "blue shirt",
        }
    )
    
    assert response.status_code == 500
    assert "LLM client" in response.json()["detail"]


@patch("services.personal_shopper_agent.retrieve_context")
@patch("api.agent.get_llm_client")
@patch("api.agent.get_search_service")
def test_recommend_with_custom_weights(mock_search, mock_llm, mock_context):
    """Test multimodal search with custom weights."""
    # Mock search service
    mock_search_instance = MagicMock()
    mock_search_instance.search_multimodal.return_value = [
        MagicMock(**result) for result in dummy_search_results()
    ]
    mock_search.return_value = mock_search_instance
    
    # Mock context retriever
    mock_context.return_value = "Mocked context"
    
    # Mock LLM client
    mock_llm_instance = MagicMock()
    mock_llm_instance.generate.return_value = dummy_llm_response()
    mock_llm.return_value = mock_llm_instance
    
    # Send request with custom weights
    response = client.post(
        "/agent/recommend?top_k=3&image_weight=0.7&text_weight=0.3",
        data={
            "user_id": "user123",
            "query": "blue shirt",
        }
    )
    
    assert response.status_code == 200
    
    # Verify search was called with custom weights
    mock_search_instance.search_multimodal.assert_called_once()
    call_kwargs = mock_search_instance.search_multimodal.call_args[1]
    assert call_kwargs["image_weight"] == 0.7
    assert call_kwargs["text_weight"] == 0.3


@patch("services.personal_shopper_agent.retrieve_context")
@patch("api.agent.get_llm_client")
@patch("api.agent.get_search_service")
def test_recommend_response_structure(mock_search, mock_llm, mock_context):
    """Test the response structure matches RecommendResponse model."""
    # Mock search service
    mock_search_instance = MagicMock()
    mock_search_instance.search_multimodal.return_value = [
        MagicMock(**result) for result in dummy_search_results()[:2]
    ]
    mock_search.return_value = mock_search_instance
    
    # Mock context retriever
    mock_context.return_value = "Mocked context"
    
    # Mock LLM client
    mock_llm_instance = MagicMock()
    mock_llm_instance.generate.return_value = dummy_llm_response()
    mock_llm.return_value = mock_llm_instance
    
    response = client.post(
        "/agent/recommend",
        data={
            "user_id": "user123",
            "query": "blue shirt",
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check all required fields are present
    assert "user_id" in data
    assert "query" in data
    assert "image_filename" in data
    assert "recommendations" in data
    assert "search_results_count" in data
    assert "llm_prompt_summary" in data
    
    # Check recommendation structure
    for rec in data["recommendations"]:
        assert "rank" in rec
        assert "title" in rec
        assert "description" in rec
        assert "is_wildcard" in rec
        assert "product_link" in rec


@patch("services.personal_shopper_agent.retrieve_context")
@patch("api.agent.get_llm_client")
@patch("api.agent.get_search_service")
def test_recommend_with_invalid_llm_response(mock_search, mock_llm, mock_context):
    """Test fallback when LLM returns invalid JSON."""
    # Mock search service
    mock_search_instance = MagicMock()
    results = [MagicMock(**result) for result in dummy_search_results()]
    mock_search_instance.search_multimodal.return_value = results
    mock_search.return_value = mock_search_instance
    
    # Mock context retriever
    mock_context.return_value = "Mocked context"
    
    # Mock LLM client with invalid response
    mock_llm_instance = MagicMock()
    mock_llm_instance.generate.return_value = "This is not JSON"
    mock_llm.return_value = mock_llm_instance
    
    response = client.post(
        "/agent/recommend",
        data={
            "user_id": "user123",
            "query": "blue shirt",
        }
    )
    
    # Should still succeed with fallback recommendations
    assert response.status_code == 200
    data = response.json()
    assert len(data["recommendations"]) > 0


def test_root_endpoint_includes_recommend():
    """Test that root endpoint includes /agent/recommend."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "recommend" in data["endpoints"]
    assert data["endpoints"]["recommend"] == "/agent/recommend"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
