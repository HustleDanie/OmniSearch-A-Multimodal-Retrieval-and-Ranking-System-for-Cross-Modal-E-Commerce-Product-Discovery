"""
FastAPI application for OmniSearch - Multimodal Product Search API.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import search_router, agent_router
from api.ab_endpoints import router as ab_router
from api.ab_search import router as ab_search_router
from api.click_analytics import router as click_analytics_router
from api.ab_middleware import ABTestingMiddleware

# Create FastAPI app
app = FastAPI(
    title="OmniSearch: Multimodal Product Discovery",
    description="A Multimodal Retrieval and Ranking System for Cross-Modal E-Commerce Product Discovery using CLIP embeddings, vector databases, and advanced ranking algorithms",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add A/B testing middleware (before CORS to capture all requests)
app.add_middleware(ABTestingMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(search_router)
app.include_router(agent_router)
app.include_router(ab_router)
app.include_router(ab_search_router)
app.include_router(click_analytics_router)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "OmniSearch API",
        "version": "1.0.0",
        "description": "Multimodal product search using CLIP embeddings",
        "endpoints": {
            "text_search": "/search/text",
            "image_search": "/search/image",
            "multimodal_search": "/search/multimodal",
            "ab_text_search": "/search-ab/text",
            "ab_image_search": "/search-ab/image",
            "ab_variants": "/search-ab/variants",
            "recommend": "/agent/recommend",
            "ab_assign": "/ab/assign",
            "ab_log_search": "/ab/log-search",
            "ab_log_click": "/ab/log-click",
            "ab_metrics": "/ab/metrics",
            "log_click": "/analytics/log-click",
            "log_impression": "/analytics/log-impression",
            "ctr": "/analytics/ctr",
            "rank_metrics": "/analytics/rank-metrics",
            "response_time": "/analytics/response-time",
            "user_analytics": "/analytics/user/{user_id}",
            "variants_comparison": "/analytics/variants-comparison",
            "health": "/search/health",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health():
    """Simple health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload during development
        log_level="info"
    )
