"""
Search variant implementations for A/B testing.

search_v1: Vector similarity only
- Pure embedding-based search
- Fast, baseline approach
- Ranking by vector similarity score

search_v2: Vector + ranking engine
- Embedding-based search + multi-factor ranking
- Considers: vector similarity, color match, category match, text similarity
- Slower but more comprehensive ranking
- Weighted scoring: 0.5*vector + 0.2*color + 0.2*category + 0.1*text
"""
from typing import List, Optional, Dict, Any
import tempfile
import os
import time
from models.search import ProductResult
from services import get_search_service
from services.ranking import rerank_results


class SearchVariantV1:
    """
    Search V1: Vector similarity only (baseline)
    
    Uses pure embedding-based search without additional ranking factors.
    Returns results ranked solely by vector similarity to the query.
    """
    
    @staticmethod
    def search_by_text(
        query_text: str,
        top_k: int = 10,
        category_filter: Optional[str] = None,
        color_filter: Optional[str] = None,
        debug: bool = False
    ) -> tuple[List[ProductResult], float]:
        """
        Search by text query using vector similarity only.
        
        Args:
            query_text: Text query string
            top_k: Number of results to return (default: 10)
            category_filter: Optional category filter
            color_filter: Optional color filter
            debug: Include debug scoring breakdown
            
        Returns:
            Tuple of (ProductResult list, search_time_ms)
        """
        start_time = time.time()
        
        try:
            search_service = get_search_service()
            
            # Use vector similarity only - disable re-ranking
            results = search_service.search_by_text(
                query_text=query_text,
                top_k=top_k,
                category_filter=category_filter,
                color_filter=color_filter,
                enable_reranking=False,  # V1: Vector similarity only
                enable_debug=debug
            )
            
            # Convert to ProductResult format
            product_results = [
                ProductResult(
                    product_id=r.product_id,
                    title=r.title,
                    description=r.description,
                    color=r.color,
                    category=r.category,
                    image_path=r.image_path,
                    similarity=r.similarity,
                    distance=r.distance,
                    debug_scores=r.debug_scores
                )
                for r in results
            ]
            
            elapsed_ms = (time.time() - start_time) * 1000
            return product_results, elapsed_ms
            
        except Exception as e:
            raise Exception(f"V1 search failed: {str(e)}")
    
    @staticmethod
    def search_by_image(
        image_path: str,
        top_k: int = 10,
        category_filter: Optional[str] = None,
        color_filter: Optional[str] = None,
        debug: bool = False
    ) -> tuple[List[ProductResult], float]:
        """
        Search by image query using vector similarity only.
        
        Args:
            image_path: Path to query image
            top_k: Number of results to return (default: 10)
            category_filter: Optional category filter
            color_filter: Optional color filter
            debug: Include debug scoring breakdown
            
        Returns:
            Tuple of (ProductResult list, search_time_ms)
        """
        start_time = time.time()
        
        try:
            search_service = get_search_service()
            
            # Use vector similarity only - disable re-ranking
            results = search_service.search_by_image(
                image_path=image_path,
                top_k=top_k,
                category_filter=category_filter,
                color_filter=color_filter,
                enable_reranking=False,  # V1: Vector similarity only
                enable_debug=debug
            )
            
            # Convert to ProductResult format
            product_results = [
                ProductResult(
                    product_id=r.product_id,
                    title=r.title,
                    description=r.description,
                    color=r.color,
                    category=r.category,
                    image_path=r.image_path,
                    similarity=r.similarity,
                    distance=r.distance,
                    debug_scores=r.debug_scores
                )
                for r in results
            ]
            
            elapsed_ms = (time.time() - start_time) * 1000
            return product_results, elapsed_ms
            
        except Exception as e:
            raise Exception(f"V1 image search failed: {str(e)}")


class SearchVariantV2:
    """
    Search V2: Vector + ranking engine
    
    Uses embedding-based search followed by multi-factor ranking.
    Considers: vector similarity, color match, category match, text-title similarity.
    Weighted scoring: 0.5*vector + 0.2*color + 0.2*category + 0.1*text
    """
    
    @staticmethod
    def search_by_text(
        query_text: str,
        top_k: int = 10,
        category_filter: Optional[str] = None,
        color_filter: Optional[str] = None,
        debug: bool = False
    ) -> tuple[List[ProductResult], float]:
        """
        Search by text query with ranking engine re-ranking.
        
        Args:
            query_text: Text query string
            top_k: Number of results to return (default: 10)
            category_filter: Optional category filter
            color_filter: Optional color filter
            debug: Include debug scoring breakdown
            
        Returns:
            Tuple of (ProductResult list, search_time_ms)
        """
        start_time = time.time()
        
        try:
            search_service = get_search_service()
            
            # Use vector similarity + ranking engine - enable re-ranking
            results = search_service.search_by_text(
                query_text=query_text,
                top_k=top_k,
                category_filter=category_filter,
                color_filter=color_filter,
                enable_reranking=True,  # V2: Enable ranking engine
                enable_debug=debug
            )
            
            # Convert to ProductResult format
            product_results = [
                ProductResult(
                    product_id=r.product_id,
                    title=r.title,
                    description=r.description,
                    color=r.color,
                    category=r.category,
                    image_path=r.image_path,
                    similarity=r.similarity,  # This is final_score from re-ranking
                    distance=r.distance,
                    debug_scores=r.debug_scores
                )
                for r in results
            ]
            
            elapsed_ms = (time.time() - start_time) * 1000
            return product_results, elapsed_ms
            
        except Exception as e:
            raise Exception(f"V2 search failed: {str(e)}")
    
    @staticmethod
    def search_by_image(
        image_path: str,
        top_k: int = 10,
        category_filter: Optional[str] = None,
        color_filter: Optional[str] = None,
        debug: bool = False
    ) -> tuple[List[ProductResult], float]:
        """
        Search by image query with ranking engine re-ranking.
        
        Args:
            image_path: Path to query image
            top_k: Number of results to return (default: 10)
            category_filter: Optional category filter
            color_filter: Optional color filter
            debug: Include debug scoring breakdown
            
        Returns:
            Tuple of (ProductResult list, search_time_ms)
        """
        start_time = time.time()
        
        try:
            search_service = get_search_service()
            
            # Use vector similarity + ranking engine - enable re-ranking
            results = search_service.search_by_image(
                image_path=image_path,
                top_k=top_k,
                category_filter=category_filter,
                color_filter=color_filter,
                enable_reranking=True,  # V2: Enable ranking engine
                enable_debug=debug
            )
            
            # Convert to ProductResult format
            product_results = [
                ProductResult(
                    product_id=r.product_id,
                    title=r.title,
                    description=r.description,
                    color=r.color,
                    category=r.category,
                    image_path=r.image_path,
                    similarity=r.similarity,  # This is final_score from re-ranking
                    distance=r.distance,
                    debug_scores=r.debug_scores
                )
                for r in results
            ]
            
            elapsed_ms = (time.time() - start_time) * 1000
            return product_results, elapsed_ms
            
        except Exception as e:
            raise Exception(f"V2 image search failed: {str(e)}")


# Mapping for A/B framework
SEARCH_VARIANTS = {
    "search_v1": SearchVariantV1,
    "search_v2": SearchVariantV2,
}


def get_search_variant(variant_name: str):
    """
    Get the search variant class by name.
    
    Args:
        variant_name: "search_v1" or "search_v2"
        
    Returns:
        The search variant class
        
    Raises:
        ValueError: If variant_name is not recognized
    """
    if variant_name not in SEARCH_VARIANTS:
        raise ValueError(f"Unknown search variant: {variant_name}. Available: {list(SEARCH_VARIANTS.keys())}")
    return SEARCH_VARIANTS[variant_name]
