"""
FastAPI routes for PersonalShopperAgent endpoints.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Form
from fastapi.responses import JSONResponse
from typing import Optional
import tempfile
import os
import json

from models.agent import RecommendRequest, RecommendResponse, Recommendation
from services import get_search_service, get_llm_client
from services.personal_shopper_agent import PersonalShopperAgent


router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/recommend", response_model=RecommendResponse)
async def recommend(
    user_id: str = Form(..., description="User ID"),
    query: Optional[str] = Form(None, description="Text search query"),
    image: Optional[UploadFile] = File(None, description="Image file for search"),
    top_k: int = Query(5, ge=1, le=20, description="Number of products to consider for recommendations"),
    image_weight: float = Query(0.6, ge=0.0, le=1.0, description="Weight for image embedding in multimodal search"),
    text_weight: float = Query(0.4, ge=0.0, le=1.0, description="Weight for text embedding in multimodal search"),
):
    """
    Generate personalized product recommendations for a user.
    
    Flow:
    1. Perform multimodal search using query and/or image
    2. Call PersonalShopperAgent with search results
    3. Generate AI-powered recommendations using LLM
    4. Return recommendations with product links
    
    Args:
        user_id: Target user identifier
        query: Optional text search query
        image: Optional image file for visual search
        top_k: Number of products to consider (default: 5)
        image_weight: Weight for image in multimodal search (default: 0.6)
        text_weight: Weight for text in multimodal search (default: 0.4)
        
    Returns:
        RecommendResponse with AI recommendations and product links
    """
    if not query and not image:
        raise HTTPException(status_code=400, detail="Provide at least one of: query text or image file")
    
    temp_path = None
    try:
        # Step 1: Perform multimodal search
        search_service = get_search_service()
        
        # Handle image if provided
        if image is not None:
            if not image.content_type or not image.content_type.startswith("image/"):
                raise HTTPException(status_code=400, detail="File must be an image")
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(image.filename)[1]) as temp_file:
                content = await image.read()
                temp_file.write(content)
                temp_path = temp_file.name
        
        # Perform multimodal search
        search_results = search_service.search_multimodal(
            text_query=(query.strip() if query else None),
            image_path=temp_path,
            image_weight=image_weight,
            text_weight=text_weight,
            top_k=top_k,
            enable_debug=False
        )
        
        # Convert search results to dict format
        search_results_dicts = [
            {
                "product_id": r.product_id,
                "title": r.title,
                "description": r.description,
                "color": r.color,
                "category": r.category,
                "image_path": r.image_path,
                "similarity": r.similarity,
                "distance": r.distance,
            }
            for r in search_results
        ]
        
        # Step 2: Get LLM client and create PersonalShopperAgent
        llm_client = get_llm_client()
        if not llm_client:
            raise HTTPException(status_code=500, detail="LLM client not configured")
        
        agent = PersonalShopperAgent(llm_client=llm_client)
        
        # Step 3: Generate recommendations
        agent_response = agent.recommend(
            user_id=user_id,
            query=(query if query else f"Visual search with image: {image.filename if image else 'unknown'}"),
            search_results=search_results_dicts,
            max_results=top_k,
        )
        
        # Step 4: Parse LLM response and build recommendations
        try:
            llm_json = json.loads(agent_response["llm_response"])
            recommendations_data = llm_json.get("recommendations", [])
        except (json.JSONDecodeError, KeyError, TypeError):
            # Fallback if LLM response isn't valid JSON
            recommendations_data = [
                {
                    "title": r["title"],
                    "why": f"Highly relevant match based on your search for '{query or 'visual similarity'}'",
                    "is_wildcard": False,
                }
                for r in search_results_dicts[:4]
            ]
        
        # Step 5: Build response with product links
        recommendations = []
        for i, rec in enumerate(recommendations_data[:4]):  # Max 4 recommendations
            # Find matching product in search results
            product_link = None
            matched_product = None
            for result in search_results_dicts:
                if result["title"].lower() == rec.get("title", "").lower():
                    product_link = f"/products/{result['product_id']}"
                    matched_product = result
                    break
            
            recommendation = Recommendation(
                rank=i + 1,
                title=rec.get("title", ""),
                description=rec.get("why", ""),
                is_wildcard=rec.get("is_wildcard", False),
                product_link=product_link,
                product_details=matched_product,
            )
            recommendations.append(recommendation)
        
        return RecommendResponse(
            user_id=user_id,
            query=query,
            image_filename=image.filename if image else None,
            recommendations=recommendations,
            search_results_count=len(search_results_dicts),
            llm_prompt_summary=agent_response["prompt"][:200] + "..." if len(agent_response["prompt"]) > 200 else agent_response["prompt"],
        )
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Recommendation generation failed: {str(e)}")
    
    finally:
        # Clean up temporary image file
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)
