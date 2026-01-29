"""
Pydantic models for PersonalShopperAgent API endpoints.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class Recommendation(BaseModel):
    """Single AI-generated recommendation."""
    
    rank: int = Field(..., description="Recommendation rank (1-4)")
    title: str = Field(..., description="Product title/name")
    description: str = Field(..., description="Why this product was recommended")
    is_wildcard: bool = Field(..., description="Whether this is a wildcard (novel) recommendation")
    product_link: Optional[str] = Field(None, description="API link to product details")
    product_details: Optional[Dict[str, Any]] = Field(None, description="Full product details from search")
    
    class Config:
        json_schema_extra = {
            "example": {
                "rank": 1,
                "title": "Blue Casual Shirt",
                "description": "Matches your preference for blue casual apparel. Comfortable cotton material.",
                "is_wildcard": False,
                "product_link": "/products/PROD-001",
                "product_details": {
                    "product_id": "PROD-001",
                    "title": "Blue Casual Shirt",
                    "color": "blue",
                    "category": "apparel",
                    "price": 49.99,
                }
            }
        }


class RecommendResponse(BaseModel):
    """Response model for recommendation endpoint."""
    
    user_id: str = Field(..., description="User ID")
    query: Optional[str] = Field(None, description="Text query used for search")
    image_filename: Optional[str] = Field(None, description="Image filename if used for search")
    recommendations: List[Recommendation] = Field(..., description="List of AI-generated recommendations (up to 4)")
    search_results_count: int = Field(..., description="Number of products considered for recommendations")
    llm_prompt_summary: str = Field(..., description="Summary of the prompt sent to LLM")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user123",
                "query": "blue casual shirt",
                "image_filename": None,
                "recommendations": [
                    {
                        "rank": 1,
                        "title": "Blue Casual Shirt",
                        "description": "Matches your preference for blue casual apparel",
                        "is_wildcard": False,
                        "product_link": "/products/PROD-001",
                    }
                ],
                "search_results_count": 5,
                "llm_prompt_summary": "You are a fashion stylist. Use user context to craft personalized picks..."
            }
        }


class RecommendRequest(BaseModel):
    """Request model for recommendation endpoint (for documentation)."""
    
    user_id: str = Field(..., description="User ID")
    query: Optional[str] = Field(None, description="Text search query")
    top_k: int = Field(5, description="Number of products to consider", ge=1, le=20)
    image_weight: float = Field(0.6, description="Weight for image in multimodal search", ge=0.0, le=1.0)
    text_weight: float = Field(0.4, description="Weight for text in multimodal search", ge=0.0, le=1.0)
