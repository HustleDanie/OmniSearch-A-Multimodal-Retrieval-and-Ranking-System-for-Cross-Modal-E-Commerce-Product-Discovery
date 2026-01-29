"""
Search Service for multimodal product search using Weaviate.
Performs vector similarity search and returns ranked results.
"""
import numpy as np
from typing import List, Dict, Any, Optional, Union
from db import WeaviateClient, WeaviateConnection
from services import get_clip_service
from services.ranking import rerank_results


class SearchResult:
    """Container for a single search result."""
    
    def __init__(self, product_data: Dict[str, Any], similarity: float, distance: float):
        """
        Initialize search result.
        
        Args:
            product_data: Product properties from Weaviate
            similarity: Similarity score (0-1, higher is better)
            distance: Distance metric from Weaviate
        """
        self.product_id = product_data.get("product_id")
        self.title = product_data.get("title")
        self.description = product_data.get("description")
        self.color = product_data.get("color")
        self.category = product_data.get("category")
        self.image_path = product_data.get("image_path")
        self.similarity = similarity
        self.distance = distance
        self.debug_scores = None  # Optional debug scoring breakdown
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        result = {
            "product_id": self.product_id,
            "title": self.title,
            "description": self.description,
            "color": self.color,
            "category": self.category,
            "image_path": self.image_path,
            "similarity": self.similarity,
            "distance": self.distance
        }
        if self.debug_scores is not None:
            result["debug_scores"] = self.debug_scores
        return result
    
    def __repr__(self) -> str:
        return f"<SearchResult: {self.product_id} - {self.title} (similarity={self.similarity:.4f})>"


class ProductSearchService:
    """Service for searching products using vector similarity."""
    
    def __init__(self, weaviate_url: Optional[str] = None):
        """
        Initialize search service.
        
        Args:
            weaviate_url: Weaviate instance URL (uses env var if None)
        """
        self.weaviate_url = weaviate_url
        self.clip_service = get_clip_service()
    
    def fuse_embeddings(self, 
                       image_vec: Optional[np.ndarray] = None,
                       text_vec: Optional[np.ndarray] = None,
                       image_weight: float = 0.6,
                       text_weight: float = 0.4) -> np.ndarray:
        """
        Fuse image and text embeddings into a single vector.
        
        Behavior:
        - If both provided: weighted average (default: 60% image, 40% text)
        - If one missing: use the available vector
        - Always normalizes the final vector
        
        Args:
            image_vec: Optional image embedding vector
            text_vec: Optional text embedding vector
            image_weight: Weight for image embedding (default: 0.6)
            text_weight: Weight for text embedding (default: 0.4)
            
        Returns:
            Normalized fused embedding vector ready for vector search
            
        Raises:
            ValueError: If neither vector is provided
        """
        if image_vec is None and text_vec is None:
            raise ValueError("At least one of image_vec or text_vec must be provided")
        
        # Case 1: Both vectors provided - weighted average
        if image_vec is not None and text_vec is not None:
            fused = image_weight * image_vec + text_weight * text_vec
        
        # Case 2: Only image vector
        elif image_vec is not None:
            fused = image_vec
        
        # Case 3: Only text vector
        else:
            fused = text_vec
        
        # Normalize to unit length
        fused_normalized = fused / np.linalg.norm(fused)
        
        return fused_normalized
    
    def search_by_vector(self, 
                        query_vector: np.ndarray,
                        top_k: int = 10,
                        category_filter: Optional[str] = None,
                        color_filter: Optional[str] = None) -> List[SearchResult]:
        """
        Search for products using a query vector.
        
        Args:
            query_vector: Query embedding vector (numpy array)
            top_k: Number of top results to return (default: 10)
            category_filter: Optional category to filter by
            color_filter: Optional color to filter by
            
        Returns:
            List of SearchResult objects, ranked by similarity
        """
        with WeaviateConnection(url=self.weaviate_url) as client:
            # Perform vector search
            filters = {}
            if category_filter:
                filters["category"] = category_filter
            if color_filter:
                filters["color"] = color_filter
            raw_results = client.search_by_vector(
                query_vector=query_vector,
                limit=top_k,
                filters=filters if filters else None
            )
            
            # Convert to SearchResult objects
            results = []
            for raw_result in raw_results:
                props = raw_result["properties"]
                
                # Server-side filters applied; client-side check kept as safety
                if category_filter and props.get("category") != category_filter:
                    continue
                if color_filter and props.get("color") != color_filter:
                    continue
                
                result = SearchResult(
                    product_data=props,
                    similarity=raw_result["similarity"],
                    distance=raw_result["distance"]
                )
                results.append(result)
            
            return results[:top_k]  # Ensure we don't exceed top_k after filtering
    
    def search_by_text(self,
                      query_text: str,
                      top_k: int = 10,
                      category_filter: Optional[str] = None,
                      color_filter: Optional[str] = None,
                      enable_reranking: bool = True,
                      enable_debug: bool = False) -> List[SearchResult]:
        """
        Search for products using text query.
        
        Args:
            query_text: Text query string
            top_k: Number of top results to return (default: 10)
            category_filter: Optional category to filter by
            color_filter: Optional color to filter by
            enable_reranking: Apply re-ranking with additional scoring factors (default: True)
            enable_debug: Include debug scoring breakdown (default: False)
            
        Returns:
            List of SearchResult objects, ranked by similarity (or final_score if reranked)
        """
        # Generate embedding from text
        query_vector = self.clip_service.embed_text(query_text)
        
        # Fetch more results for re-ranking
        fetch_limit = max(30, top_k * 3) if enable_reranking else top_k
        
        # Perform vector search
        initial_results = self.search_by_vector(
            query_vector=query_vector,
            top_k=fetch_limit,
            category_filter=category_filter,
            color_filter=color_filter
        )
        
        if not enable_reranking or len(initial_results) == 0:
            return initial_results[:top_k]
        
        # Re-rank using additional factors
        result_dicts = [r.to_dict() for r in initial_results]
        reranked_dicts = rerank_results(
            results=result_dicts,
            query_text=query_text,
            query_color=color_filter,
            query_category=category_filter,
            add_score_field=True,
            add_debug_scores=enable_debug
        )
        
        # Convert back to SearchResult objects, update similarity with final_score
        reranked_results = []
        for rd in reranked_dicts[:top_k]:
            result = SearchResult(
                product_data=rd,
                similarity=rd.get("final_score", rd.get("similarity", 0.0)),
                distance=rd.get("distance", 0.0)
            )
            # Preserve debug scores if present
            if "debug_scores" in rd:
                result.debug_scores = rd["debug_scores"]
            reranked_results.append(result)
        
        return reranked_results
    
    def search_by_image(self,
                       image_path: str,
                       top_k: int = 10,
                       category_filter: Optional[str] = None,
                       color_filter: Optional[str] = None,
                       enable_reranking: bool = True,
                       enable_debug: bool = False) -> List[SearchResult]:
        """
        Search for products using an image query.
        
        Args:
            image_path: Path to query image
            top_k: Number of top results to return (default: 10)
            category_filter: Optional category to filter by
            color_filter: Optional color to filter by
            enable_reranking: Apply re-ranking with additional scoring factors (default: True)
            enable_debug: Include debug scoring breakdown (default: False)
            
        Returns:
            List of SearchResult objects, ranked by similarity (or final_score if reranked)
        """
        # Generate embedding from image
        query_vector = self.clip_service.embed_image(image_path)
        
        # Fetch more results for re-ranking
        fetch_limit = max(30, top_k * 3) if enable_reranking else top_k
        
        # Perform vector search
        initial_results = self.search_by_vector(
            query_vector=query_vector,
            top_k=fetch_limit,
            category_filter=category_filter,
            color_filter=color_filter
        )
        
        if not enable_reranking or len(initial_results) == 0:
            return initial_results[:top_k]
        
        # Re-rank (no query_text for image-only search)
        result_dicts = [r.to_dict() for r in initial_results]
        reranked_dicts = rerank_results(
            results=result_dicts,
            query_text=None,
            query_color=color_filter,
            query_category=category_filter,
            add_score_field=True,
            add_debug_scores=enable_debug
        )
        
        # Convert back to SearchResult objects
        reranked_results = []
        for rd in reranked_dicts[:top_k]:
            result = SearchResult(
                product_data=rd,
                similarity=rd.get("final_score", rd.get("similarity", 0.0)),
                distance=rd.get("distance", 0.0)
            )
            if "debug_scores" in rd:
                result.debug_scores = rd["debug_scores"]
            reranked_results.append(result)
        
        return reranked_results
    
    def search_multimodal(self,
                         text_query: Optional[str] = None,
                         image_path: Optional[str] = None,
                         image_weight: float = 0.6,
                         text_weight: float = 0.4,
                         top_k: int = 10,
                         category_filter: Optional[str] = None,
                         color_filter: Optional[str] = None,
                         enable_reranking: bool = True,
                         enable_debug: bool = False) -> List[SearchResult]:
        """
        Search using both text and image queries combined.
        
        Args:
            text_query: Optional text query string
            image_path: Optional path to query image
            image_weight: Weight for image embedding (default: 0.6)
            text_weight: Weight for text embedding (default: 0.4)
            top_k: Number of top results to return (default: 10)
            category_filter: Optional category to filter by
            color_filter: Optional color to filter by
            enable_reranking: Apply re-ranking with additional scoring factors (default: True)
            enable_debug: Include debug scoring breakdown (default: False)
            
        Returns:
            List of SearchResult objects, ranked by similarity (or final_score if reranked)
            
        Raises:
            ValueError: If neither text nor image query is provided
        """
        if text_query is None and image_path is None:
            raise ValueError("Must provide at least one of text_query or image_path")
        
        # Generate embeddings
        text_vec = None
        image_vec = None
        
        if text_query:
            text_vec = self.clip_service.embed_text(text_query)
        
        if image_path:
            image_vec = self.clip_service.embed_image(image_path)
        
        # Fuse embeddings using the new fusion function
        fused_vector = self.fuse_embeddings(
            image_vec=image_vec,
            text_vec=text_vec,
            image_weight=image_weight,
            text_weight=text_weight
        )
        
        # Fetch more results for re-ranking
        fetch_limit = max(30, top_k * 3) if enable_reranking else top_k
        
        # Perform vector search
        initial_results = self.search_by_vector(
            query_vector=fused_vector,
            top_k=fetch_limit,
            category_filter=category_filter,
            color_filter=color_filter
        )
        
        if not enable_reranking or len(initial_results) == 0:
            return initial_results[:top_k]
        
        # Re-rank using text query if available
        result_dicts = [r.to_dict() for r in initial_results]
        reranked_dicts = rerank_results(
            results=result_dicts,
            query_text=text_query,
            query_color=color_filter,
            query_category=category_filter,
            add_score_field=True,
            add_debug_scores=enable_debug
        )
        
        # Convert back to SearchResult objects
        reranked_results = []
        for rd in reranked_dicts[:top_k]:
            result = SearchResult(
                product_data=rd,
                similarity=rd.get("final_score", rd.get("similarity", 0.0)),
                distance=rd.get("distance", 0.0)
            )
            if "debug_scores" in rd:
                result.debug_scores = rd["debug_scores"]
            reranked_results.append(result)
        
        return reranked_results
    
    def format_results(self, results: List[SearchResult]) -> List[Dict[str, Any]]:
        """
        Format search results as list of dictionaries.
        
        Args:
            results: List of SearchResult objects
            
        Returns:
            List of result dictionaries
        """
        return [result.to_dict() for result in results]
    
    def print_results(self, results: List[SearchResult], show_scores: bool = True) -> None:
        """
        Pretty print search results.
        
        Args:
            results: List of SearchResult objects
            show_scores: Whether to display similarity scores
        """
        if not results:
            print("No results found.")
            return
        
        print(f"\nFound {len(results)} results:\n")
        print("=" * 80)
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result.title}")
            print(f"   Product ID: {result.product_id}")
            print(f"   Category: {result.category} | Color: {result.color}")
            print(f"   Description: {result.description}")
            
            if show_scores:
                print(f"   Similarity: {result.similarity:.4f} | Distance: {result.distance:.4f}")
            
            if result.image_path:
                print(f"   Image: {result.image_path}")
        
        print("\n" + "=" * 80)


# Singleton instance for reuse
_search_service: Optional[ProductSearchService] = None


def get_search_service(weaviate_url: Optional[str] = None) -> ProductSearchService:
    """
    Get or create singleton search service instance.
    
    Args:
        weaviate_url: Weaviate instance URL
        
    Returns:
        ProductSearchService instance
    """
    global _search_service
    
    if _search_service is None:
        _search_service = ProductSearchService(weaviate_url=weaviate_url)
    
    return _search_service
