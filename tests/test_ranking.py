"""
Unit tests for the ranking module.

Tests verify:
1. Exact color match ranks higher
2. Category match affects ordering
3. Text similarity changes scores
"""
import pytest
import numpy as np
from typing import List, Dict, Any
import sys
from pathlib import Path
import importlib.util

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Import ranking module directly without triggering services/__init__.py
ranking_path = str(parent_dir / "services" / "ranking.py")
spec = importlib.util.spec_from_file_location("ranking_module", ranking_path)
ranking_module = importlib.util.module_from_spec(spec)
sys.modules['ranking_module'] = ranking_module
spec.loader.exec_module(ranking_module)

# Get the functions we need
text_similarity = ranking_module.text_similarity
exact_match_boost = ranking_module.exact_match_boost
compute_final_score = ranking_module.compute_final_score
rerank_results = ranking_module.rerank_results
cosine_similarity_embeddings = ranking_module.cosine_similarity_embeddings


class MockSearchResult:
    """Mock search result for testing."""
    def __init__(
        self,
        product_id: str,
        title: str,
        category: str,
        color: str,
        similarity: float,
        distance: float = None,
        title_embedding: List[float] = None
    ):
        self.product_id = product_id
        self.title = title
        self.category = category
        self.color = color
        self.similarity = similarity
        self.distance = distance if distance is not None else (1.0 - similarity)
        self.title_embedding = title_embedding or [0.0] * 512
        self.description = f"Description for {title}"
        self.image_path = f"/images/{product_id}.jpg"
        self.final_score = None
        self.debug_scores = None


class TestColorMatchRanking:
    """Test that exact color match ranks products higher."""
    
    def test_color_match_beats_higher_similarity(self):
        """Product with color match should rank higher even with lower vector similarity"""
        results = [
            MockSearchResult(
                product_id="prod1",
                title="Red Cotton Shirt",
                category="shirts",
                color="red",
                similarity=0.85  # Higher vector similarity
            ),
            MockSearchResult(
                product_id="prod2",
                title="Blue Silk Shirt",
                category="shirts",
                color="blue",
                similarity=0.75  # Lower vector similarity but matches filter
            )
        ]
        
        reranked = rerank_results(
            results=results,
            query_text="blue shirt",
            query_color="blue",
            query_category=None
        )
        
        # Product with matching color should rank first
        assert reranked[0]["product_id"] == "prod2"
        assert reranked[1]["product_id"] == "prod1"
        # Verify the color-matched product has higher final score
        assert reranked[0]["final_score"] > reranked[1]["final_score"]
    
    def test_color_match_with_equal_similarity(self):
        """With equal similarity, color match should be tiebreaker"""
        results = [
            MockSearchResult(
                product_id="prod1",
                title="Green Dress",
                category="dresses",
                color="green",
                similarity=0.80
            ),
            MockSearchResult(
                product_id="prod2",
                title="Blue Dress",
                category="dresses",
                color="blue",
                similarity=0.80
            )
        ]
        
        reranked = rerank_results(
            results=results,
            query_text="dress",
            query_color="blue",
            query_category=None
        )
        
        # Blue dress should rank higher due to color match
        assert reranked[0]["product_id"] == "prod2"
        assert reranked[0]["final_score"] > reranked[1]["final_score"]


class TestCategoryMatchRanking:
    """Test that category match affects ordering."""
    
    def test_category_match_boosts_ranking(self):
        """Product matching category filter should rank higher"""
        results = [
            MockSearchResult(
                product_id="prod1",
                title="Running Shoes",
                category="shoes",
                color="black",
                similarity=0.80
            ),
            MockSearchResult(
                product_id="prod2",
                title="Summer Dress",
                category="dresses",
                color="black",
                similarity=0.75
            )
        ]
        
        reranked = rerank_results(
            results=results,
            query_text="black clothing",
            query_color=None,
            query_category="dresses"
        )
        
        # Dress should rank higher due to category match
        assert reranked[0]["product_id"] == "prod2"
        assert reranked[0]["final_score"] > reranked[1]["final_score"]
    
    def test_category_and_color_combined(self):
        """Both category and color matches should provide maximum boost"""
        results = [
            MockSearchResult(
                product_id="prod1",
                title="Red Shirt",
                category="shirts",
                color="red",
                similarity=0.70  # Lower similarity
            ),
            MockSearchResult(
                product_id="prod2",
                title="Blue Dress",
                category="dresses",
                color="blue",
                similarity=0.85  # Higher similarity but no filter matches
            ),
            MockSearchResult(
                product_id="prod3",
                title="Blue Shirt",
                category="shirts",
                color="blue",
                similarity=0.75  # Medium similarity but both filters match
            )
        ]
        
        reranked = rerank_results(
            results=results,
            query_text="shirt",
            query_color="blue",
            query_category="shirts"
        )
        
        # Product matching both filters should rank first
        assert reranked[0]["product_id"] == "prod3"
        # Verify it has the highest final score
        assert reranked[0]["final_score"] > reranked[1]["final_score"]
        assert reranked[0]["final_score"] > reranked[2]["final_score"]


class TestTextSimilarityScoring:
    """Test that text similarity changes scores."""
    
    def test_text_similarity_affects_score(self):
        """Products with matching keywords should score higher"""
        results = [
            MockSearchResult(
                product_id="prod1",
                title="Generic Product",  # No matching keywords
                category="misc",
                color="white",
                similarity=0.75
            ),
            MockSearchResult(
                product_id="prod2",
                title="Blue Running Shoes",  # Matching keywords
                category="misc",
                color="white",
                similarity=0.75  # Same vector similarity
            )
        ]
        
        reranked = rerank_results(
            results=results,
            query_text="blue running shoes",
            query_color=None,
            query_category=None
        )
        
        # Product with matching title should rank higher
        assert reranked[0]["product_id"] == "prod2"
        assert reranked[0]["final_score"] > reranked[1]["final_score"]
    
    def test_partial_text_match(self):
        """Partial text matches should provide proportional boost"""
        results = [
            MockSearchResult(
                product_id="prod1",
                title="Blue Dress",  # 1/3 match
                category="dresses",
                color="blue",
                similarity=0.70
            ),
            MockSearchResult(
                product_id="prod2",
                title="Blue Evening Dress",  # 2/3 match
                category="dresses",
                color="blue",
                similarity=0.70
            )
        ]
        
        reranked = rerank_results(
            results=results,
            query_text="blue evening dress",
            query_color=None,
            query_category=None
        )
        
        # Better text match should rank higher
        assert reranked[0]["product_id"] == "prod2"
        # Verify text similarity component is higher
        text_sim1 = text_similarity("blue evening dress", "Blue Dress")
        text_sim2 = text_similarity("blue evening dress", "Blue Evening Dress")
        assert text_sim2 > text_sim1
    
    def test_text_similarity_with_filters(self):
        """Text similarity should work alongside filter boosts"""
        results = [
            MockSearchResult(
                product_id="prod1",
                title="Item",  # Matches color but not text
                category="misc",
                color="red",
                similarity=0.75
            ),
            MockSearchResult(
                product_id="prod2",
                title="Red Velvet Cake",  # Matches both color and text
                category="misc",
                color="red",
                similarity=0.75
            )
        ]
        
        reranked = rerank_results(
            results=results,
            query_text="red velvet cake",
            query_color="red",
            query_category=None
        )
        
        # Product with both color match and text match should rank higher
        assert reranked[0]["product_id"] == "prod2"
        assert reranked[0]["final_score"] > reranked[1]["final_score"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
