"""
FastAPI routes for product search endpoints.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Form
from fastapi.responses import JSONResponse
from typing import Optional
import tempfile
import os

from models.search import (
    TextSearchRequest,
    SearchResponse,
    ImageSearchResponse,
    ProductResult,
    HealthResponse,
    MultimodalSearchResponse
)
from services import get_search_service, get_clip_service
from db import WeaviateClient


router = APIRouter(prefix="/search", tags=["search"])


@router.post("/text", response_model=SearchResponse)
async def search_by_text(request: TextSearchRequest):
    """
    Search for products using text query.
    
    The text query is converted to an embedding using CLIP, then used to find
    the most similar products in the vector database.
    
    Args:
        request: TextSearchRequest with query, top_k, and optional filters
        
    Returns:
        SearchResponse with matching products and similarity scores
    """
    try:
        # Get search service
        search_service = get_search_service()
        
        # Perform search
        results = search_service.search_by_text(
            query_text=request.query,
            top_k=request.top_k,
            category_filter=request.category,
            color_filter=request.color,
            enable_debug=request.debug
        )
        
        # Convert to response model
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
        
        return SearchResponse(
            query=request.query,
            results=product_results,
            total_results=len(product_results)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/image", response_model=ImageSearchResponse)
async def search_by_image(
    file: UploadFile = File(...),
    top_k: int = Query(10, ge=1, le=100, description="Number of results to return"),
    category: Optional[str] = Query(None, description="Filter by category"),
    color: Optional[str] = Query(None, description="Filter by color"),
    debug: bool = Query(False, description="Include debug scoring breakdown")
):
    """
    Search for products using an uploaded image.
    
    The image is converted to an embedding using CLIP, then used to find
    the most similar products in the vector database.
    
    Args:
        file: Uploaded image file (JPEG, PNG, etc.)
        top_k: Number of results to return (default: 10)
        category: Optional category filter
        color: Optional color filter
        
    Returns:
        ImageSearchResponse with matching products and similarity scores
    """
    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Save uploaded file temporarily
    temp_path = None
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            # Read and write file content
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        # Get search service
        search_service = get_search_service()
        
        # Perform search
        results = search_service.search_by_image(
            image_path=temp_path,
            top_k=top_k,
            category_filter=category,
            color_filter=color,
            enable_debug=debug
        )
        
        # Convert to response model
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
        
        return ImageSearchResponse(
            filename=file.filename,
            results=product_results,
            total_results=len(product_results)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image search failed: {str(e)}")
        
    finally:
        # Clean up temporary file
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)


@router.post("/multimodal", response_model=MultimodalSearchResponse)
async def search_multimodal(
    file: UploadFile | None = File(None, description="Optional image file"),
    text: str | None = Form(None, description="Optional text query"),
    top_k: int = Query(10, ge=1, le=100, description="Number of results to return"),
    category: Optional[str] = Query(None, description="Filter by category"),
    color: Optional[str] = Query(None, description="Filter by color"),
    image_weight: float = Query(0.6, ge=0.0, le=1.0, description="Weight for image embedding"),
    text_weight: float = Query(0.4, ge=0.0, le=1.0, description="Weight for text embedding"),
    debug: bool = Query(False, description="Include debug scoring breakdown")
):
    """
    Multimodal search endpoint that accepts optional image and/or text.
    
    Steps:
    - Generate embeddings for provided modalities
    - Fuse them via weighted average (default 0.6 image, 0.4 text)
    - Query Weaviate with the fused vector
    - Return product results with similarity scores
    """
    if not file and (text is None or text.strip() == ""):
        raise HTTPException(status_code=400, detail="Provide at least one of: image file or text query")

    temp_path = None
    try:
        # If image is provided, persist to a temp file path
        if file is not None:
            if not file.content_type or not file.content_type.startswith("image/"):
                raise HTTPException(status_code=400, detail="File must be an image")
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
                content = await file.read()
                temp_file.write(content)
                temp_path = temp_file.name

        # Perform multimodal search via service (handles fusion internally)
        search_service = get_search_service()
        results = search_service.search_multimodal(
            text_query=(text.strip() if text else None),
            image_path=temp_path,
            image_weight=image_weight,
            text_weight=text_weight,
            top_k=top_k,
            category_filter=category,
            color_filter=color,
            enable_debug=debug
        )

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

        return MultimodalSearchResponse(
            text=text,
            filename=(file.filename if file else None),
            results=product_results,
            total_results=len(product_results)
        )

    except HTTPException:
        # Re-raise validation errors
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Multimodal search failed: {str(e)}")
    finally:
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Check the health status of the search service.
    
    Returns:
        HealthResponse with service status information
    """
    try:
        # Check CLIP service
        clip_service = get_clip_service()
        clip_loaded = clip_service is not None
        
        # Check Weaviate connection
        weaviate_connected = False
        try:
            weaviate_client = WeaviateClient()
            weaviate_client.connect()
            weaviate_connected = weaviate_client.client.is_ready()
            weaviate_client.disconnect()
        except Exception:
            pass
        
        status = "healthy" if (clip_loaded and weaviate_connected) else "degraded"
        
        return HealthResponse(
            status=status,
            clip_loaded=clip_loaded,
            weaviate_connected=weaviate_connected
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")
