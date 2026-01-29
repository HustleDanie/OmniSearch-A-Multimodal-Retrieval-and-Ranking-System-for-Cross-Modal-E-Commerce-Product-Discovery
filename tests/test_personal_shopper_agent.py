"""
Tests for PersonalShopperAgent.
"""
import pytest
from unittest.mock import MagicMock, patch

from services.personal_shopper_agent import PersonalShopperAgent


def dummy_search_results():
    return [
        {
            "title": "Blue Casual Shirt",
            "description": "Comfortable cotton shirt",
            "color": "blue",
            "category": "apparel",
            "price": 49.99,
            "score": 0.95,
        },
        {
            "title": "Black Formal Blazer",
            "description": "Sharp tailored blazer",
            "color": "black",
            "category": "apparel",
            "price": 129.99,
            "score": 0.90,
        },
    ]


def test_recommend_with_provided_results():
    llm_client = MagicMock()
    llm_client.generate.return_value = "{\"recommendations\": []}"

    agent = PersonalShopperAgent(llm_client=llm_client)

    with patch("services.personal_shopper_agent.retrieve_context") as mock_retrieve:
        mock_retrieve.return_value = "Mocked context text"
        
        response = agent.recommend(
            user_id="user123",
            search_results=dummy_search_results(),
            max_results=2,
        )

        assert response["context"] == "Mocked context text"
        llm_client.generate.assert_called_once()
        assert response["search_results"]


def test_recommend_via_search_service():
    llm_client = MagicMock()
    llm_client.generate.return_value = "{\"recommendations\": []}"

    search_service = MagicMock()
    search_service.search.return_value = dummy_search_results()

    agent = PersonalShopperAgent(llm_client=llm_client, search_service=search_service)

    with patch("services.personal_shopper_agent.retrieve_context") as mock_retrieve:
        mock_retrieve.return_value = "Mocked context"
        
        response = agent.recommend(
            user_id="user123",
            query="blue shirt",
            max_results=2,
        )

        search_service.search.assert_called_once()
        assert response["search_results"][0]["title"] == "Blue Casual Shirt"


def test_missing_inputs_raise_error():
    llm_client = MagicMock()
    llm_client.generate.return_value = "{}"

    agent = PersonalShopperAgent(llm_client=llm_client)

    with pytest.raises(ValueError):
        agent.recommend(user_id="user123", max_results=2)


def test_custom_prompt_template():
    llm_client = MagicMock()
    llm_client.generate.return_value = "{}"

    agent = PersonalShopperAgent(llm_client=llm_client)

    template = "PREFS:\n{{context}}\nEND"
    
    with patch("services.personal_shopper_agent.retrieve_context") as mock_retrieve:
        mock_retrieve.return_value = "User preferences and search results"
        
        resp = agent.recommend(
            user_id="user123",
            search_results=dummy_search_results(),
            prompt_template=template,
        )

        assert resp["prompt"].startswith("PREFS:")
        assert resp["prompt"].endswith("END")
