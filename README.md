# OmniSearch: A Multimodal Retrieval and Ranking System for Cross-Modal E-Commerce Product Discovery

A production-grade FastAPI-based platform for intelligent product search using CLIP embeddings, vector similarity matching, and advanced ranking algorithms. Enables seamless cross-modal search (text-to-image, image-to-image) with RAG-powered personalized recommendations.

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the API Server
```bash
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Access the API

- **API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### POST /search/text
Search for products using text query.

**Request Body:**
```json
{
  "query": "red athletic shoes",
  "top_k": 10,
  "category": "footwear",
  "color": "red"
}
```

**Response:**
```json
{
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
```

### POST /search/image
Search for products using an uploaded image.

**Request:**
- Form data with image file upload
- Query parameters: `top_k`, `category`, `color`

**Response:**
```json
{
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
```

### GET /search/health
Check service health status.

## Testing

Run the test script:
```bash
python scripts/test_api.py
```

Or use curl:

**Text Search:**
```bash
curl -X POST "http://localhost:8000/search/text" \
  -H "Content-Type: application/json" \
  -d '{"query": "red shoes", "top_k": 5}'
```

**Image Search:**
```bash
curl -X POST "http://localhost:8000/search/image?top_k=5" \
  -F "file=@path/to/image.jpg"
```

## Architecture Overview

### Cross-Modal Search

OmniSearch enables search across different modalities (text, images, or both) using a unified embedding space. The system leverages OpenAI's CLIP (Contrastive Language-Image Pre-training) model, which maps both text and images into a shared 512-dimensional vector space where semantically similar concepts are close together.

**Key Capabilities:**
- **Text Search**: Query using natural language ("red evening dress")
- **Image Search**: Query using product photos
- **Multimodal Search**: Combine text and image for refined results

All modalities are comparable because CLIP embeddings preserve semantic similarity across text and images.

### Fusion Embeddings

When both text and image inputs are provided, the system creates a **fused embedding** by combining individual embeddings with configurable weights:

```python
fused_embedding = (image_weight × image_embedding) + (text_weight × text_embedding)
```

**Default Weights:**
- Image: 60% (0.6) - Visual features dominate
- Text: 40% (0.4) - Textual context refines

**Example Use Case:**
```json
{
  "text": "formal occasion",
  "image": "[uploaded dress photo]",
  "image_weight": 0.7,
  "text_weight": 0.3
}
```

This allows users to find products that match both the visual style (from image) and the contextual intent (from text), such as finding formal dresses similar to an uploaded photo.

### Ranking Logic

The system uses a **two-stage ranking pipeline** to deliver relevant results:

#### Stage 1: Vector Retrieval (Weaviate)
- Retrieves **top 30 candidates** using cosine similarity
- Applies server-side filters (color, category) to reduce candidate set
- Uses HNSW indexing for fast approximate nearest neighbor search

#### Stage 2: Re-ranking (Custom Scorer)
- Computes weighted final score for each candidate
- Sorts by final score and returns **top 10 results**

**Scoring Formula:**
```
final_score = 0.5 × vector_similarity 
            + 0.2 × color_match 
            + 0.2 × category_match 
            + 0.1 × text_similarity
```

**Component Breakdown:**

| Component | Weight | Description |
|-----------|--------|-------------|
| **Vector Similarity** | 0.5 | Cosine similarity between query and product embeddings (CLIP) |
| **Color Match** | 0.2 | Binary boost: 1.0 if product color matches filter, 0.0 otherwise |
| **Category Match** | 0.2 | Binary boost: 1.0 if product category matches filter, 0.0 otherwise |
| **Text Similarity** | 0.1 | Bag-of-words cosine similarity between query text and product title |

**Example Ranking:**
```
Query: "blue running shoes" (color=blue, category=shoes)

Product A: Blue Casual Shoes
- Vector: 0.75, Color: 1.0, Category: 1.0, Text: 0.85
- Final Score: 0.375 + 0.2 + 0.2 + 0.085 = 0.860

Product B: Red Running Shoes  
- Vector: 0.90, Color: 0.0, Category: 1.0, Text: 0.90
- Final Score: 0.450 + 0.0 + 0.2 + 0.090 = 0.740

Result: Product A ranks higher due to color match bonus
```

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           CLIENT REQUEST                                │
│                   (Text / Image / Text+Image)                          │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         FastAPI Endpoints                               │
│  ┌──────────────┬──────────────┬─────────────────────────────────────┐ │
│  │ /search/text │ /search/image│ /search/multimodal                  │ │
│  └──────────────┴──────────────┴─────────────────────────────────────┘ │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      CLIP Embedding Service                             │
│                    (OpenAI CLIP ViT-B/32)                               │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  Text Input  → [512-dim embedding]                               │  │
│  │  Image Input → [512-dim embedding]                               │  │
│  │  Both        → Fused Embedding (weighted sum)                    │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        Search Service                                   │
│                     (ProductSearchService)                              │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  1. Apply filters (category, color)                             │  │
│  │  2. Query vector DB                                              │  │
│  │  3. Get top 30 candidates                                        │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       Weaviate Vector DB                                │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  • HNSW Index for fast similarity search                         │  │
│  │  • Product schema with manual vectorization                      │  │
│  │  • Cosine similarity metric                                      │  │
│  │  • Server-side filtering on metadata                             │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼ (Top 30 Results)
┌─────────────────────────────────────────────────────────────────────────┐
│                        Ranking Module                                   │
│                     (services/ranking.py)                               │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  For each result:                                                │  │
│  │    • Compute vector_similarity (CLIP)                            │  │
│  │    • Compute color_match (exact match bonus)                     │  │
│  │    • Compute category_match (exact match bonus)                  │  │
│  │    • Compute text_similarity (bag-of-words)                      │  │
│  │    • Calculate final_score (weighted sum)                        │  │
│  │                                                                   │  │
│  │  Sort by final_score descending                                  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼ (Top 10 Results)
┌─────────────────────────────────────────────────────────────────────────┐
│                          API RESPONSE                                   │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  {                                                                │  │
│  │    "results": [                                                   │  │
│  │      {                                                            │  │
│  │        "product_id": "...",                                       │  │
│  │        "title": "...",                                            │  │
│  │        "similarity": 0.85,                                        │  │
│  │        "debug_scores": {  // if debug=true                        │  │
│  │          "vector_score": 0.85,                                    │  │
│  │          "color_score": 0.2,                                      │  │
│  │          "category_score": 0.2,                                   │  │
│  │          "text_score": 0.08,                                      │  │
│  │          "final_score": 0.73                                      │  │
│  │        }                                                          │  │
│  │      }                                                            │  │
│  │    ]                                                              │  │
│  │  }                                                                │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘

                    Data Storage (Parallel to Search)
                    ┌────────────────────────────────┐
                    │      MongoDB                   │
                    │  (Product Metadata)            │
                    │  • Title, description          │
                    │  • Color, category             │
                    │  • Image paths                 │
                    └────────────────────────────────┘
```

### Key Design Decisions

1. **Manual Vectorization**: Embeddings are generated offline and stored in Weaviate, avoiding runtime CLIP inference overhead
2. **Two-Stage Ranking**: Vector retrieval for recall, custom scoring for precision
3. **Configurable Weights**: Fusion and ranking weights can be tuned per use case
4. **Debug Mode**: Transparent scoring breakdown for explainability
5. **Filter-First Strategy**: Server-side filtering reduces candidates before re-ranking

## User Profiles

OmniSearch includes a user profile system to track preferences and purchase history for personalized recommendations.

### Schema

```json
{
  "user_id": "USER-001",
  "past_purchases": ["Blue Running Shoes", "Cotton T-Shirt"],
  "preferred_colors": ["blue", "black"],
  "preferred_categories": ["footwear", "apparel"],
  "price_range": {"min": 20, "max": 200}
}
```

### Core Functions

| Function | Description |
|----------|-------------|
| `create_user_profile()` | Create new user with preferences |
| `get_user_profile()` | Retrieve user profile by user_id |
| `update_preferences()` | Update colors, categories, price range |
| `add_purchase()` | Record product purchase in history |

### Usage Example

```python
from db.user_service import UserProfileService

service = UserProfileService()
service.connect()

# Create user profile
user = service.create_user_profile(
    user_id="USER-001",
    past_purchases=["Blue Shoes"],
    preferred_colors=["blue", "black"],
    preferred_categories=["footwear"],
    price_range={"min": 20, "max": 200}
)

# Update preferences
service.update_preferences(
    user_id="USER-001",
    price_range={"min": 25, "max": 250}
)

# Record a purchase
service.add_purchase("USER-001", "Running Socks")

# Retrieve updated profile
user = service.get_user_profile("USER-001")
print(f"Purchases: {user['past_purchases']}")
```

See [USER_PROFILES.md](USER_PROFILES.md) for complete API documentation.

## Project Structure

```
omnisearch/
├── main.py                      # FastAPI application
├── api/
│   └── search.py               # Search endpoints
├── services/
│   ├── clip_service.py         # CLIP embedding service
│   ├── search_service.py       # Vector search orchestration
│   └── ranking.py              # Re-ranking and scoring logic
├── db/
│   ├── mongodb.py              # MongoDB products collection
│   ├── user_service.py         # User profile service
│   └── weaviate_client.py      # Weaviate vector DB client
├── models/
│   ├── product.py              # Product schemas
│   ├── user.py                 # User profile schemas
│   └── search.py               # API request/response models
├── scripts/
│   ├── generate_embeddings.py  # ETL pipeline for embeddings
│   ├── test_user_service.py    # User service manual tests
│   └── test_api.py             # API test suite
└── tests/
    ├── test_ranking.py         # Unit tests for ranking logic
    └── test_user_profiles.py   # Unit tests for user profiles
```
