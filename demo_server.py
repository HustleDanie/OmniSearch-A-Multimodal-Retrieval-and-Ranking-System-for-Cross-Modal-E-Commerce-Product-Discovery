"""
Quick Start Demo for OmniSearch
Runs API with mock services (no Docker required)
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn

# Create FastAPI app
app = FastAPI(
    title="OmniSearch API - Demo Mode",
    description="Multimodal product search API (Demo Mode - Mock Data)",
    version="1.0.0-demo",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock Data Models
class Product(BaseModel):
    product_id: str
    title: str
    description: str
    color: str
    category: str
    image_path: str
    similarity: float
    distance: float

class TextSearchRequest(BaseModel):
    query: str
    top_k: int = 10
    category: Optional[str] = None
    color: Optional[str] = None
    debug: bool = False

class SearchResponse(BaseModel):
    query: str
    results: List[Product]
    total_results: int

# Mock product database
MOCK_PRODUCTS = [
    {
        "product_id": "P001",
        "title": "Elegant Red Summer Dress",
        "description": "Beautiful red dress perfect for summer occasions",
        "color": "red",
        "category": "dresses",
        "image_path": "/images/red_dress_001.jpg",
        "similarity": 0.95,
        "distance": 0.05
    },
    {
        "product_id": "P002",
        "title": "Classic Blue Denim Jeans",
        "description": "Comfortable blue jeans with modern fit",
        "color": "blue",
        "category": "pants",
        "image_path": "/images/blue_jeans_002.jpg",
        "similarity": 0.89,
        "distance": 0.11
    },
    {
        "product_id": "P003",
        "title": "White Cotton T-Shirt",
        "description": "Soft cotton t-shirt in classic white",
        "color": "white",
        "category": "tops",
        "image_path": "/images/white_tshirt_003.jpg",
        "similarity": 0.87,
        "distance": 0.13
    },
    {
        "product_id": "P004",
        "title": "Black Leather Sneakers",
        "description": "Stylish black sneakers with leather finish",
        "color": "black",
        "category": "shoes",
        "image_path": "/images/black_sneakers_004.jpg",
        "similarity": 0.92,
        "distance": 0.08
    },
    {
        "product_id": "P005",
        "title": "Floral Print Maxi Dress",
        "description": "Flowing maxi dress with beautiful floral pattern",
        "color": "multicolor",
        "category": "dresses",
        "image_path": "/images/floral_dress_005.jpg",
        "similarity": 0.91,
        "distance": 0.09
    },
]

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "OmniSearch API - Demo Mode",
        "version": "1.0.0-demo",
        "status": "running",
        "mode": "demo",
        "message": "This is a demo version with mock data. Install Docker for full functionality.",
        "endpoints": {
            "text_search": "/search/text",
            "health": "/search/health",
            "docs": "/docs"
        }
    }

@app.get("/search/health")
async def health_check():
    """Check the health status of the demo service."""
    return {
        "status": "healthy",
        "mode": "demo",
        "clip_loaded": False,
        "weaviate_connected": False,
        "message": "Running in demo mode with mock data"
    }

@app.post("/search/text", response_model=SearchResponse)
async def search_by_text(request: TextSearchRequest):
    """
    Search for products using text query (DEMO MODE - Returns mock data).
    
    In production, this would:
    1. Convert text to CLIP embedding
    2. Search vector database
    3. Return real product matches
    
    Demo mode returns filtered mock products.
    """
    # Filter mock products based on request
    filtered_products = MOCK_PRODUCTS.copy()
    
    # Apply category filter
    if request.category:
        filtered_products = [p for p in filtered_products if p["category"] == request.category]
    
    # Apply color filter
    if request.color:
        filtered_products = [p for p in filtered_products if p["color"] == request.color]
    
    # Simple keyword matching for demo
    query_lower = request.query.lower()
    scored_products = []
    for product in filtered_products:
        score = 0.0
        if query_lower in product["title"].lower():
            score += 0.5
        if query_lower in product["description"].lower():
            score += 0.3
        if any(word in product["title"].lower() or word in product["description"].lower() 
               for word in query_lower.split()):
            score += 0.2
        
        if score > 0:
            product = product.copy()
            product["similarity"] = min(0.99, 0.70 + score)
            product["distance"] = 1 - product["similarity"]
            scored_products.append(product)
    
    # If no matches, return all products
    if not scored_products:
        scored_products = filtered_products
    
    # Sort by similarity
    scored_products.sort(key=lambda x: x["similarity"], reverse=True)
    
    # Limit to top_k
    results = scored_products[:request.top_k]
    
    return SearchResponse(
        query=request.query,
        results=[Product(**p) for p in results],
        total_results=len(results)
    )

@app.get("/demo/info")
async def demo_info():
    """Information about demo mode."""
    return {
        "mode": "demo",
        "features": {
            "text_search": "✓ Available (mock data)",
            "image_search": "✗ Requires CLIP model",
            "multimodal_search": "✗ Requires CLIP model",
            "ai_agent": "✗ Requires LLM",
            "vector_db": "✗ Requires Weaviate",
            "user_profiles": "✗ Requires MongoDB"
        },
        "setup_instructions": {
            "full_version": "Install Docker Desktop and run: docker-compose up -d",
            "docker_url": "https://www.docker.com/products/docker-desktop/"
        },
        "mock_products": len(MOCK_PRODUCTS),
        "available_categories": list(set(p["category"] for p in MOCK_PRODUCTS)),
        "available_colors": list(set(p["color"] for p in MOCK_PRODUCTS))
    }

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 OmniSearch Demo Mode Starting...")
    print("=" * 60)
    print()
    print("📍 API URL:      http://localhost:8000")
    print("📖 Interactive:  http://localhost:8000/docs")
    print("ℹ️  Demo Info:    http://localhost:8000/demo/info")
    print()
    print("⚠️  DEMO MODE: Using mock data")
    print("   For full functionality, install Docker and run:")
    print("   docker-compose up -d")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 60)
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
