"""
API endpoints for click tracking and metrics analysis.

Provides endpoints to:
- Log click events on search results
- Query click-through rates
- Analyze result ranking effectiveness
- Monitor response times
- Compare variant performance
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from services.click_tracking import (
    get_click_tracker,
    ClickEvent,
    SearchImpression,
    ClickSource
)
from api.ab_middleware import get_user_id, get_session_id


router = APIRouter(prefix="/analytics", tags=["analytics"])


# Pydantic models
class ClickLogRequest(BaseModel):
    """Request to log a click event."""
    product_id: str = Field(..., description="Product that was clicked")
    rank: int = Field(..., ge=0, description="Position of result (0-based)")
    search_query: str = Field(..., description="Original search query")
    variant: str = Field(..., description="Variant that served results (search_v1 or search_v2)")
    response_time_ms: float = Field(..., ge=0, description="Response time in milliseconds")
    source: Optional[str] = Field(default="search_results", description="Click source")


class ImpressionLogRequest(BaseModel):
    """Request to log a search impression."""
    query: str = Field(..., description="Search query executed")
    variant: str = Field(..., description="Variant used (search_v1 or search_v2)")
    results_count: int = Field(..., ge=0, description="Number of results returned")
    response_time_ms: float = Field(..., ge=0, description="Response time in milliseconds")


class CTRResponse(BaseModel):
    """Click-through rate response."""
    ctr: float = Field(..., description="Overall CTR (0.0-1.0)")
    clicks: int = Field(..., description="Total clicks")
    impressions: int = Field(..., description="Total impressions")
    period_days: int = Field(..., description="Analysis period in days")
    ctr_search_v1: Optional[float] = Field(None, description="CTR for search_v1")
    ctr_search_v2: Optional[float] = Field(None, description="CTR for search_v2")
    clicks_search_v1: Optional[int] = Field(None, description="Clicks for search_v1")
    clicks_search_v2: Optional[int] = Field(None, description="Clicks for search_v2")


class RankMetricsResponse(BaseModel):
    """Result ranking metrics."""
    avg_rank: float = Field(..., description="Average rank of clicked results")
    median_rank: Optional[int] = Field(None, description="Median rank")
    min_rank: Optional[int] = Field(None, description="Minimum rank clicked")
    max_rank: Optional[int] = Field(None, description="Maximum rank clicked")
    clicks_by_rank: dict = Field(..., description="Distribution of clicks by rank")
    total_clicks: int = Field(..., description="Total clicks analyzed")


class ResponseTimeMetricsResponse(BaseModel):
    """Response time statistics."""
    avg_response_time_ms: float = Field(..., description="Average response time")
    min_response_time_ms: Optional[float] = Field(None, description="Minimum response time")
    max_response_time_ms: Optional[float] = Field(None, description="Maximum response time")
    p95_response_time_ms: Optional[float] = Field(None, description="95th percentile")
    count: int = Field(..., description="Number of measurements")


class UserSummaryResponse(BaseModel):
    """User analytics summary."""
    user_id: str = Field(..., description="User ID")
    period_days: int = Field(..., description="Analysis period")
    total_clicks: int = Field(..., description="Total clicks")
    total_impressions: int = Field(..., description="Total search impressions")
    ctr: float = Field(..., description="Click-through rate")
    avg_rank_clicked: float = Field(..., description="Average rank of clicked results")
    avg_response_time_ms: float = Field(..., description="Average response time")
    variants_used: list = Field(..., description="Variants used by this user")


class VariantComparisonResponse(BaseModel):
    """Comparison between variants."""
    period_days: int = Field(..., description="Analysis period")
    variants: dict = Field(..., description="Metrics for each variant")
    winner_by_ctr: str = Field(..., description="Variant with higher CTR")


@router.post("/log-click")
async def log_click(
    request: ClickLogRequest,
    user_id: str = Depends(get_user_id),
    session_id: Optional[str] = Depends(get_session_id)
) -> dict:
    """
    Log a click event on a search result.
    
    This endpoint records when a user clicks on a search result, including:
    - Which result was clicked (by rank/position)
    - What search query led to it
    - Which variant served the results
    - Response time for that search
    
    The data is used to calculate click-through rates and analyze ranking effectiveness.
    
    Args:
        product_id: ID of the product that was clicked
        rank: Position in results (0 = first result)
        search_query: Original search query
        variant: Which variant returned the results (search_v1 or search_v2)
        response_time_ms: Response time of the search
        source: Where the click came from (optional)
        
    Returns:
        Confirmation of logged click
        
    Example (curl):
        curl -X POST "http://localhost:8000/analytics/log-click" \\
          -H "X-User-ID: user123" \\
          -H "Content-Type: application/json" \\
          -d '{
            "product_id": "prod_001",
            "rank": 0,
            "search_query": "blue shoes",
            "variant": "search_v1",
            "response_time_ms": 45.2
          }'
    """
    try:
        tracker = get_click_tracker()
        
        click_event = ClickEvent(
            user_id=user_id,
            product_id=request.product_id,
            rank=request.rank,
            search_query=request.search_query,
            variant=request.variant,
            response_time_ms=request.response_time_ms,
            session_id=session_id,
            source=request.source or ClickSource.SEARCH_RESULTS.value
        )
        
        success = tracker.log_click(click_event)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to log click event"
            )
        
        return {
            "status": "success",
            "user_id": user_id,
            "product_id": request.product_id,
            "rank": request.rank,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Click logging failed: {str(e)}")


@router.post("/log-impression")
async def log_impression(
    request: ImpressionLogRequest,
    user_id: str = Depends(get_user_id),
    session_id: Optional[str] = Depends(get_session_id)
) -> dict:
    """
    Log a search impression (query executed).
    
    This endpoint records when a user performs a search, including:
    - The search query
    - Which variant served the results
    - Number of results returned
    - Response time
    
    Impressions are used with click events to calculate CTR.
    
    Args:
        query: Search query executed
        variant: Which variant returned results (search_v1 or search_v2)
        results_count: How many results were returned
        response_time_ms: Response time in milliseconds
        
    Returns:
        Confirmation of logged impression
        
    Example (curl):
        curl -X POST "http://localhost:8000/analytics/log-impression" \\
          -H "X-User-ID: user123" \\
          -H "Content-Type: application/json" \\
          -d '{
            "query": "blue shoes",
            "variant": "search_v1",
            "results_count": 10,
            "response_time_ms": 45.2
          }'
    """
    try:
        tracker = get_click_tracker()
        
        impression = SearchImpression(
            user_id=user_id,
            query=request.query,
            variant=request.variant,
            results_count=request.results_count,
            response_time_ms=request.response_time_ms,
            session_id=session_id
        )
        
        success = tracker.log_impression(impression)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to log impression event"
            )
        
        return {
            "status": "success",
            "user_id": user_id,
            "query": request.query,
            "variant": request.variant,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Impression logging failed: {str(e)}")


@router.get("/ctr", response_model=dict)
async def get_ctr(
    user_id: Optional[str] = Query(None, description="Filter by user"),
    variant: Optional[str] = Query(None, description="Filter by variant (search_v1 or search_v2)"),
    days: int = Query(7, ge=1, le=365, description="Look back period (1-365 days)")
) -> dict:
    """
    Get click-through rate metrics.
    
    Calculates CTR as: clicks / impressions
    
    Args:
        user_id: Filter to specific user (optional)
        variant: Filter to specific variant (optional)
        days: Look back period in days (default 7)
        
    Returns:
        CTR metrics with breakdowns by variant
        
    Example (curl):
        curl "http://localhost:8000/analytics/ctr?days=7"
        curl "http://localhost:8000/analytics/ctr?variant=search_v1&days=14"
        curl "http://localhost:8000/analytics/ctr?user_id=user123"
    """
    try:
        tracker = get_click_tracker()
        metrics = tracker.get_ctr(user_id=user_id, variant=variant, days=days)
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CTR calculation failed: {str(e)}")


@router.get("/rank-metrics", response_model=dict)
async def get_rank_metrics(
    user_id: Optional[str] = Query(None, description="Filter by user"),
    variant: Optional[str] = Query(None, description="Filter by variant"),
    days: int = Query(7, ge=1, le=365, description="Look back period")
) -> dict:
    """
    Get result ranking metrics.
    
    Shows statistics about which ranks/positions get clicked:
    - Average rank of clicked results
    - Distribution of clicks by rank
    - Minimum and maximum ranks clicked
    
    Lower average rank = better ranking (results people want are near top)
    
    Args:
        user_id: Filter by user (optional)
        variant: Filter by variant (optional)
        days: Look back period in days
        
    Returns:
        Ranking statistics
        
    Example (curl):
        curl "http://localhost:8000/analytics/rank-metrics?days=7"
        curl "http://localhost:8000/analytics/rank-metrics?variant=search_v2"
    """
    try:
        tracker = get_click_tracker()
        metrics = tracker.get_rank_metrics(user_id=user_id, variant=variant, days=days)
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rank metrics failed: {str(e)}")


@router.get("/response-time", response_model=dict)
async def get_response_time(
    user_id: Optional[str] = Query(None, description="Filter by user"),
    variant: Optional[str] = Query(None, description="Filter by variant"),
    days: int = Query(7, ge=1, le=365, description="Look back period")
) -> dict:
    """
    Get response time statistics.
    
    Shows performance metrics for search latency:
    - Average response time
    - Min/max/95th percentile
    - Number of measurements
    
    Args:
        user_id: Filter by user (optional)
        variant: Filter by variant (optional)
        days: Look back period in days
        
    Returns:
        Response time statistics
        
    Example (curl):
        curl "http://localhost:8000/analytics/response-time"
        curl "http://localhost:8000/analytics/response-time?variant=search_v2"
    """
    try:
        tracker = get_click_tracker()
        metrics = tracker.get_response_time_metrics(
            user_id=user_id,
            variant=variant,
            days=days
        )
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Response time metrics failed: {str(e)}")


@router.get("/user/{user_id}", response_model=dict)
async def get_user_analytics(
    user_id: str,
    days: int = Query(7, ge=1, le=365, description="Look back period")
) -> dict:
    """
    Get comprehensive analytics for a specific user.
    
    Shows all metrics for a user:
    - Click count and impressions
    - CTR
    - Average rank of clicks
    - Response times
    - Variants used
    
    Args:
        user_id: User ID to analyze
        days: Look back period in days
        
    Returns:
        Complete user analytics summary
        
    Example (curl):
        curl "http://localhost:8000/analytics/user/user123"
        curl "http://localhost:8000/analytics/user/user456?days=14"
    """
    try:
        tracker = get_click_tracker()
        summary = tracker.get_user_summary(user_id, days=days)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"User analytics failed: {str(e)}")


@router.get("/variants-comparison", response_model=dict)
async def get_variants_comparison(
    days: int = Query(7, ge=1, le=365, description="Look back period")
) -> dict:
    """
    Compare performance between search variants.
    
    Shows side-by-side comparison of search_v1 vs search_v2:
    - Click-through rates
    - Ranking effectiveness (average rank clicked)
    - Response times
    - Which variant wins on CTR
    
    Use this to evaluate if V2 is better than V1.
    
    Args:
        days: Look back period in days
        
    Returns:
        Variant comparison metrics
        
    Example (curl):
        curl "http://localhost:8000/analytics/variants-comparison"
        curl "http://localhost:8000/analytics/variants-comparison?days=14"
    """
    try:
        tracker = get_click_tracker()
        comparison = tracker.get_variant_comparison(days=days)
        return comparison
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Variant comparison failed: {str(e)}")


@router.delete("/reset")
async def reset_data() -> dict:
    """
    Reset all click tracking data.
    
    **WARNING**: This permanently deletes all recorded clicks and impressions!
    
    Use only for:
    - Testing
    - Resetting after development
    - Clearing stale data before new test
    
    Returns:
        Confirmation message
        
    Example (curl):
        curl -X DELETE "http://localhost:8000/analytics/reset"
    """
    try:
        tracker = get_click_tracker()
        success = tracker.reset()
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to reset data"
            )
        
        return {
            "status": "success",
            "message": "All click tracking data deleted",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")
