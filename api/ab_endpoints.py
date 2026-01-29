"""
A/B Testing API endpoints.

Exposes assignment, logging, and metrics endpoints.
"""

from fastapi import APIRouter, Request, Depends, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import time

from services.ab_testing import (
    get_experiment_manager,
    ExperimentVariant,
    SearchEvent,
    ClickEvent
)
from api.ab_middleware import get_user_id, get_session_id

router = APIRouter(prefix="/ab", tags=["A/B Testing"])


# Response Models
class VariantAssignment(BaseModel):
    """User's variant assignment."""
    user_id: str
    variant: str
    assigned_at: str
    metadata: Dict[str, Any] = {}


class SearchLogRequest(BaseModel):
    """Request to log a search event."""
    query: str
    results_count: int
    search_time_ms: Optional[float] = 0.0


class ClickLogRequest(BaseModel):
    """Request to log a click event."""
    product_id: str
    product_title: Optional[str] = ""
    position: Optional[int] = -1
    query: Optional[str] = None


class EventResponse(BaseModel):
    """Base event response."""
    event_type: str
    user_id: str
    variant: str
    timestamp: str


class MetricsResponse(BaseModel):
    """Aggregate metrics response."""
    total_events: int
    total_assignments: int
    search_events: int
    click_events: int
    search_v1: Dict[str, Any]
    search_v2: Dict[str, Any]
    avg_search_time_ms: float
    avg_results: float


# Endpoints
@router.post("/assign", response_model=VariantAssignment)
async def assign_variant(
    request: Request,
    user_id: str = Query(None, description="User ID (optional, auto-generated if not provided)")
) -> Dict[str, Any]:
    """
    Assign a user to an experiment variant.
    
    If user_id not provided, uses from request header or generates new.
    If already assigned, returns existing assignment.
    
    **Query Parameters:**
    - `user_id`: Optional user identifier
    
    **Returns:**
    - user_id: User identifier
    - variant: Assigned variant (search_v1 or search_v2)
    - assigned_at: ISO timestamp
    - metadata: Additional metadata
    
    **Example:**
    ```bash
    curl "http://localhost:8000/ab/assign?user_id=user123"
    ```
    """
    manager = get_experiment_manager()
    
    # Use provided user_id or extract from request
    if not user_id:
        user_id = getattr(request.state, 'user_id', None)
    
    assignment = manager.assign_variant(user_id)
    return assignment.to_dict()


@router.post("/log-search", response_model=EventResponse)
async def log_search(
    request: Request,
    body: SearchLogRequest,
    user_id: str = Depends(get_user_id),
    session_id: str = Depends(get_session_id)
) -> Dict[str, Any]:
    """
    Log a search query event.
    
    **Request Body:**
    - `query`: Search query string (required)
    - `results_count`: Number of results returned (required)
    - `search_time_ms`: Search execution time in milliseconds (optional)
    
    **Returns:**
    - event_type: "search"
    - user_id: User who performed search
    - variant: Assigned variant
    - timestamp: ISO timestamp
    
    **Example:**
    ```bash
    curl -X POST "http://localhost:8000/ab/log-search" \\
      -H "X-User-ID: user123" \\
      -H "Content-Type: application/json" \\
      -d '{"query":"casual shirts","results_count":24,"search_time_ms":145.5}'
    ```
    """
    manager = get_experiment_manager()
    
    start_time = time.time()
    event = manager.log_search(
        user_id=user_id,
        query=body.query,
        results_count=body.results_count,
        search_time_ms=body.search_time_ms,
        session_id=session_id
    )
    
    return {
        "event_type": "search",
        "user_id": event.user_id,
        "variant": event.variant.value,
        "timestamp": event.timestamp.isoformat()
    }


@router.post("/log-click", response_model=EventResponse)
async def log_click(
    request: Request,
    body: ClickLogRequest,
    user_id: str = Depends(get_user_id),
    session_id: str = Depends(get_session_id)
) -> Dict[str, Any]:
    """
    Log a click/interaction event.
    
    **Request Body:**
    - `product_id`: Product identifier (required)
    - `product_title`: Product title (optional)
    - `position`: Position in results, 0-indexed, -1 if unknown (optional)
    - `query`: Original search query (optional)
    
    **Returns:**
    - event_type: "click"
    - user_id: User who clicked
    - variant: Assigned variant
    - timestamp: ISO timestamp
    
    **Example:**
    ```bash
    curl -X POST "http://localhost:8000/ab/log-click" \\
      -H "X-User-ID: user123" \\
      -H "Content-Type: application/json" \\
      -d '{
        "product_id":"prod_456",
        "product_title":"Blue Casual Shirt",
        "position":0,
        "query":"casual shirts"
      }'
    ```
    """
    manager = get_experiment_manager()
    
    event = manager.log_click(
        user_id=user_id,
        product_id=body.product_id,
        product_title=body.product_title,
        position=body.position,
        query=body.query,
        session_id=session_id
    )
    
    return {
        "event_type": "click",
        "user_id": event.user_id,
        "variant": event.variant.value,
        "timestamp": event.timestamp.isoformat()
    }


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics() -> Dict[str, Any]:
    """
    Get aggregate metrics for the A/B test.
    
    **Returns:**
    - total_events: Total events logged
    - total_assignments: Total users assigned
    - search_events: Total search events
    - click_events: Total click events
    - search_v1: Metrics for variant 1 (count, clicks, click-through rate)
    - search_v2: Metrics for variant 2 (count, clicks, click-through rate)
    - avg_search_time_ms: Average search time
    - avg_results: Average number of results per search
    
    **Example:**
    ```bash
    curl "http://localhost:8000/ab/metrics"
    ```
    """
    manager = get_experiment_manager()
    return manager.get_metrics()


@router.get("/assignment")
async def get_assignment(
    request: Request,
    user_id: str = Query(None, description="User ID (optional)")
) -> Dict[str, Any]:
    """
    Get assignment for a user.
    
    **Query Parameters:**
    - `user_id`: User identifier (optional, uses from header if not provided)
    
    **Returns:**
    - user_id: User identifier
    - variant: Assigned variant
    - assigned_at: ISO timestamp
    - metadata: Additional metadata
    
    **Example:**
    ```bash
    curl "http://localhost:8000/ab/assignment?user_id=user123"
    ```
    """
    manager = get_experiment_manager()
    
    # Use provided or extract from request
    if not user_id:
        user_id = getattr(request.state, 'user_id', None)
    
    assignment = manager.get_assignment(user_id)
    
    if not assignment:
        return {"error": "No assignment found", "user_id": user_id}
    
    return assignment.to_dict()


@router.get("/events")
async def get_events(
    user_id: str = Query(None, description="Filter by user ID"),
    variant: str = Query(None, description="Filter by variant (search_v1 or search_v2)"),
    event_type: str = Query(None, description="Filter by event type (search or click)"),
    limit: int = Query(100, description="Maximum events to return")
) -> Dict[str, Any]:
    """
    Get logged events from in-memory storage.
    
    **Query Parameters:**
    - `user_id`: Filter by user ID (optional)
    - `variant`: Filter by variant: search_v1, search_v2 (optional)
    - `event_type`: Filter by event type: search, click (optional)
    - `limit`: Maximum events to return (default: 100)
    
    **Returns:**
    - events: List of matching events
    - count: Number of events returned
    
    **Example:**
    ```bash
    curl "http://localhost:8000/ab/events?user_id=user123&limit=50"
    ```
    """
    manager = get_experiment_manager()
    
    # Convert variant string to enum if provided
    variant_enum = None
    if variant:
        try:
            variant_enum = ExperimentVariant(variant)
        except ValueError:
            return {"error": f"Invalid variant: {variant}"}
    
    events = manager.get_events(
        user_id=user_id,
        variant=variant_enum,
        event_type=event_type,
        limit=limit
    )
    
    return {
        "events": [e.to_dict() for e in events],
        "count": len(events)
    }


@router.delete("/reset")
async def reset():
    """
    Reset all in-memory A/B testing data.
    
    **Warning:** This clears all assignments and events. Use with caution.
    
    **Returns:**
    - success: True if reset completed
    
    **Example:**
    ```bash
    curl -X DELETE "http://localhost:8000/ab/reset"
    ```
    """
    manager = get_experiment_manager()
    manager.reset()
    return {"success": True, "message": "A/B testing data cleared"}
