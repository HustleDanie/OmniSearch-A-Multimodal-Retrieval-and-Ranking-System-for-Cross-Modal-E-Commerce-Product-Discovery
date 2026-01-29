"""
A/B Testing integrated search endpoints.

These endpoints use the A/B testing framework to assign variants (search_v1 or search_v2)
and log search events with performance metrics.

The middleware automatically injects the user's assigned variant into the request.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Depends, Request
from fastapi.responses import JSONResponse
from typing import Optional
import tempfile
import os
import time

from models.search import SearchResponse, ImageSearchResponse, ProductResult
from services.ab_testing import get_experiment_manager, ExperimentVariant
from services.search_variants import get_search_variant
from api.ab_middleware import inject_variant, get_user_id, get_session_id


router = APIRouter(prefix="/search-ab", tags=["search-ab"])


@router.post("/text", response_model=SearchResponse)
async def search_by_text_ab(
    request: Request,
    query: str = Query(..., min_length=1, description="Text search query"),
    top_k: int = Query(10, ge=1, le=100, description="Number of results"),
    category: Optional[str] = Query(None, description="Filter by category"),
    color: Optional[str] = Query(None, description="Filter by color"),
    debug: bool = Query(False, description="Include debug scoring"),
    variant: str = Depends(inject_variant),
    user_id: str = Depends(get_user_id),
    session_id: Optional[str] = Depends(get_session_id),
):
    """
    Search for products by text using A/B testing variant.
    
    The user is assigned a variant (search_v1 or search_v2) and the search
    request is executed using that variant. The search event is logged for
    metrics tracking.
    
    Args:
        query: Text search query (required)
        top_k: Number of results to return (1-100, default 10)
        category: Optional category filter
        color: Optional color filter
        debug: Include debug scoring breakdown
        
    Returns:
        SearchResponse with results and metrics
        
    Example (curl):
        curl -X POST "http://localhost:8000/search-ab/text?query=blue%20shoes&top_k=5" \\
          -H "X-User-ID: user123"
    """
    try:
        # Map variant name to ExperimentVariant enum
        variant_enum = ExperimentVariant.SEARCH_V1 if variant == "search_v1" else ExperimentVariant.SEARCH_V2
        
        # Get search variant implementation
        search_variant = get_search_variant(variant)
        
        # Execute search with timing
        start_time = time.time()
        results, search_time_ms = search_variant.search_by_text(
            query_text=query,
            top_k=top_k,
            category_filter=category,
            color_filter=color,
            debug=debug
        )
        
        # Log search event to A/B testing framework
        manager = get_experiment_manager()
        manager.log_search(
            user_id=user_id,
            query=query,
            results_count=len(results),
            search_time_ms=search_time_ms,
            session_id=session_id
        )
        
        return SearchResponse(
            query=query,
            results=results,
            total_results=len(results)
        )
        
    except ValueError as e:
        # Variant not found
        raise HTTPException(status_code=400, detail=f"Invalid variant: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/image", response_model=ImageSearchResponse)
async def search_by_image_ab(
    request: Request,
    file: UploadFile = File(...),
    top_k: int = Query(10, ge=1, le=100, description="Number of results"),
    category: Optional[str] = Query(None, description="Filter by category"),
    color: Optional[str] = Query(None, description="Filter by color"),
    debug: bool = Query(False, description="Include debug scoring"),
    variant: str = Depends(inject_variant),
    user_id: str = Depends(get_user_id),
    session_id: Optional[str] = Depends(get_session_id),
):
    """
    Search for products by image using A/B testing variant.
    
    The user is assigned a variant (search_v1 or search_v2) and the search
    request is executed using that variant. The search event is logged for
    metrics tracking.
    
    Args:
        file: Uploaded image file (required)
        top_k: Number of results to return (1-100, default 10)
        category: Optional category filter
        color: Optional color filter
        debug: Include debug scoring breakdown
        
    Returns:
        ImageSearchResponse with results and metrics
        
    Example (curl):
        curl -X POST "http://localhost:8000/search-ab/image?top_k=5" \\
          -H "X-User-ID: user123" \\
          -F "file=@/path/to/image.jpg"
    """
    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    temp_path = None
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        # Get search variant implementation
        search_variant = get_search_variant(variant)
        
        # Execute search with timing
        start_time = time.time()
        results, search_time_ms = search_variant.search_by_image(
            image_path=temp_path,
            top_k=top_k,
            category_filter=category,
            color_filter=color,
            debug=debug
        )
        
        # Log search event to A/B testing framework
        manager = get_experiment_manager()
        manager.log_search(
            user_id=user_id,
            query=f"[image: {file.filename}]",
            results_count=len(results),
            search_time_ms=search_time_ms,
            session_id=session_id
        )
        
        return ImageSearchResponse(
            filename=file.filename,
            results=results,
            total_results=len(results)
        )
        
    except ValueError as e:
        # Variant not found
        raise HTTPException(status_code=400, detail=f"Invalid variant: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image search failed: {str(e)}")
    finally:
        # Clean up temporary file
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)


@router.get("/variants")
async def get_available_variants():
    """
    Get list of available search variants.
    
    Returns:
        Dict with list of variants and descriptions
        
    Example response:
        {
            "variants": [
                {
                    "name": "search_v1",
                    "description": "Vector similarity only (baseline)"
                },
                {
                    "name": "search_v2",
                    "description": "Vector + ranking engine (enhanced)"
                }
            ]
        }
    """
    return {
        "variants": [
            {
                "name": "search_v1",
                "description": "Vector similarity only (baseline approach)"
            },
            {
                "name": "search_v2",
                "description": "Vector + ranking engine (enhanced with color/category/text scoring)"
            }
        ]
    }


@router.get("/variant-info/{variant_name}")
async def get_variant_info(variant_name: str):
    """
    Get detailed information about a search variant.
    
    Args:
        variant_name: "search_v1" or "search_v2"
        
    Returns:
        Dict with variant details
        
    Example response for search_v1:
        {
            "name": "search_v1",
            "type": "baseline",
            "description": "Pure vector similarity search",
            "scoring_factors": ["vector_similarity"],
            "reranking_enabled": false
        }
    """
    try:
        variant = get_search_variant(variant_name)
        
        if variant_name == "search_v1":
            return {
                "name": "search_v1",
                "type": "baseline",
                "description": "Vector similarity only",
                "scoring_factors": ["vector_similarity"],
                "reranking_enabled": False,
                "speed": "fast",
                "best_for": "Quick, simple similarity-based retrieval"
            }
        elif variant_name == "search_v2":
            return {
                "name": "search_v2",
                "type": "enhanced",
                "description": "Vector + multi-factor ranking",
                "scoring_factors": [
                    "vector_similarity (0.5)",
                    "color_match (0.2)",
                    "category_match (0.2)",
                    "text_similarity (0.1)"
                ],
                "reranking_enabled": True,
                "speed": "standard",
                "best_for": "Comprehensive ranking with semantic and metadata matching"
            }
        else:
            raise ValueError(f"Unknown variant: {variant_name}")
            
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
