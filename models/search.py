from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class TextSearchRequest(BaseModel):
    """Request model for text-based search."""
    
    query: str = Field(..., description="Text query for product search", min_length=1)
    top_k: int = Field(10, description="Number of results to return", ge=1, le=100)
    category: Optional[str] = Field(None, description="Filter by category")
    color: Optional[str] = Field(None, description="Filter by color")
    debug: bool = Field(False, description="Include debug scoring breakdown")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "red athletic shoes",
                "top_k": 10,
                "category": "footwear",
                "color": "red"
            }
        }


class ProductResult(BaseModel):
    """Single product search result."""
    
    product_id: str = Field(..., description="Unique product identifier")
    title: str = Field(..., description="Product title")
    description: str = Field(..., description="Product description")
    color: str = Field(..., description="Product color")
    category: str = Field(..., description="Product category")
    image_path: str = Field(..., description="Path to product image")
    similarity: float = Field(..., description="Similarity score (0-1)")
    distance: float = Field(..., description="Distance metric from vector search")
    debug_scores: Optional[Dict[str, float]] = Field(None, description="Debug scoring breakdown (if debug=true)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "product_id": "PROD-001",
                "title": "Red Running Shoes",
                "description": "Lightweight running shoes in red",
                "color": "red",
                "category": "footwear",
                "image_path": "/images/products/shoes-001.jpg",
                "similarity": 0.8542,
                "distance": 0.1458
            }
        }


class SearchResponse(BaseModel):
    """Response model for search results."""
    
    query: str = Field(..., description="Original search query")
    results: List[ProductResult] = Field(..., description="List of matching products")
    total_results: int = Field(..., description="Total number of results returned")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "red athletic shoes",
                "results": [
                    {
                        "product_id": "PROD-001",
                        "title": "Red Running Shoes",
                        "description": "Lightweight running shoes",
                        "color": "red",
                        "category": "footwear",
                        "image_path": "/images/products/shoes-001.jpg",
                        "similarity": 0.8542,
                        "distance": 0.1458
                    }
                ],
                "total_results": 1
            }
        }


class ImageSearchResponse(BaseModel):
    """Response model for image-based search results."""
    
    filename: str = Field(..., description="Uploaded image filename")
    results: List[ProductResult] = Field(..., description="List of matching products")
    total_results: int = Field(..., description="Total number of results returned")
    
    class Config:
        json_schema_extra = {
            "example": {
                "filename": "query_image.jpg",
                "results": [
                    {
                        "product_id": "PROD-001",
                        "title": "Red Running Shoes",
                        "description": "Lightweight running shoes",
                        "color": "red",
                        "category": "footwear",
                        "image_path": "/images/products/shoes-001.jpg",
                        "similarity": 0.8542,
                        "distance": 0.1458
                    }
                ],
                "total_results": 1
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""
    
    status: str = Field(..., description="Service status")
    clip_loaded: bool = Field(..., description="Whether CLIP model is loaded")
    weaviate_connected: bool = Field(..., description="Whether Weaviate is accessible")


class MultimodalSearchResponse(BaseModel):
    """Response model for multimodal search (text and/or image)."""
    
    text: Optional[str] = Field(None, description="Submitted text query, if any")
    filename: Optional[str] = Field(None, description="Uploaded image filename, if any")
    results: List[ProductResult] = Field(..., description="List of matching products")
    total_results: int = Field(..., description="Total number of results returned")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "blue denim jacket",
                "filename": "query_image.jpg",
                "results": [
                    {
                        "product_id": "PROD-010",
                        "title": "Blue Denim Jacket",
                        "description": "Classic blue denim jacket",
                        "color": "blue",
                        "category": "apparel",
                        "image_path": "/images/products/jacket-010.jpg",
                        "similarity": 0.9032,
                        "distance": 0.0968
                    }
                ],
                "total_results": 1
            }
        }
