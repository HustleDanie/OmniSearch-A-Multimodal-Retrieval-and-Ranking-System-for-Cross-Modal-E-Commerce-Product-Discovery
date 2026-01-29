# POST /agent/recommend

AI-powered product recommendation endpoint that combines multimodal search with personalized LLM recommendations.

## Overview

The `/agent/recommend` endpoint orchestrates a complete recommendation workflow:

1. **Multimodal Search**: Performs semantic search using text query and/or image
2. **Context Retrieval**: Formats user preferences and search results for LLM
3. **LLM Generation**: Calls AI to generate personalized recommendations
4. **Response Formatting**: Returns structured recommendations with product links

## Request

### Parameters

**Form Data:**
- `user_id` (string, required): Unique user identifier
- `query` (string, optional): Text search query (e.g., "blue casual shirt")
- `image` (file, optional): Product image file for visual search

**Query Parameters:**
- `top_k` (integer, default: 5, range: 1-20): Number of products to consider for recommendations
- `image_weight` (float, default: 0.6, range: 0.0-1.0): Weight for image embedding in multimodal search
- `text_weight` (float, default: 0.4, range: 0.0-1.0): Weight for text embedding in multimodal search

### Requirements
- At least one of `query` or `image` must be provided
- User must provide `user_id`

### Example Requests

**Text Query:**
```bash
curl -X POST http://localhost:8000/agent/recommend \
  -F "user_id=user123" \
  -F "query=blue casual shirt" \
  -G -d "top_k=5"
```

**Image Search:**
```bash
curl -X POST http://localhost:8000/agent/recommend \
  -F "user_id=user123" \
  -F "image=@/path/to/image.jpg" \
  -G -d "top_k=5"
```

**Multimodal (Text + Image):**
```bash
curl -X POST http://localhost:8000/agent/recommend \
  -F "user_id=user123" \
  -F "query=casual" \
  -F "image=@/path/to/image.jpg" \
  -G -d "top_k=5&image_weight=0.7&text_weight=0.3"
```

## Response

### Success (200 OK)

```json
{
  "user_id": "user123",
  "query": "blue casual shirt",
  "image_filename": null,
  "recommendations": [
    {
      "rank": 1,
      "title": "Blue Casual Shirt",
      "description": "Matches your preference for blue casual apparel. Comfortable cotton material perfect for everyday wear.",
      "is_wildcard": false,
      "product_link": "/products/PROD-001",
      "product_details": {
        "product_id": "PROD-001",
        "title": "Blue Casual Shirt",
        "description": "Comfortable cotton shirt",
        "color": "blue",
        "category": "apparel",
        "image_path": "/images/products/shirt-001.jpg",
        "similarity": 0.95,
        "distance": 0.05
      }
    },
    {
      "rank": 2,
      "title": "Black Formal Blazer",
      "description": "Complements your style with a professional piece that works with multiple outfits.",
      "is_wildcard": false,
      "product_link": "/products/PROD-002",
      "product_details": {...}
    },
    {
      "rank": 3,
      "title": "Navy Chinos",
      "description": "Versatile neutral piece that pairs well with your casual preferences.",
      "is_wildcard": false,
      "product_link": "/products/PROD-003",
      "product_details": {...}
    },
    {
      "rank": 4,
      "title": "Vintage Denim Jacket",
      "description": "A wildcard piece that adds character and edge to your wardrobe while maintaining your style sensibility.",
      "is_wildcard": true,
      "product_link": "/products/PROD-004",
      "product_details": {...}
    }
  ],
  "search_results_count": 5,
  "llm_prompt_summary": "You are a fashion/product stylist. Use the user context to craft personalized picks..."
}
```

### Response Fields

**Top-level:**
- `user_id` (string): The user ID from request
- `query` (string|null): The text query used
- `image_filename` (string|null): Name of image file if uploaded
- `recommendations` (array): List of AI-generated recommendations (max 4)
- `search_results_count` (integer): Number of products considered
- `llm_prompt_summary` (string): First 200 chars of LLM prompt for transparency

**Recommendation Object:**
- `rank` (integer): Position in recommendations (1-4)
- `title` (string): Product name/title
- `description` (string): Why this product was recommended
- `is_wildcard` (boolean): Whether this is a novel/unexpected recommendation
- `product_link` (string|null): API link to product details
- `product_details` (object|null): Full product information from search

### Error Responses

**400 Bad Request** - Missing required inputs:
```json
{
  "detail": "Provide at least one of: query text or image file"
}
```

**400 Bad Request** - Invalid file type:
```json
{
  "detail": "File must be an image"
}
```

**500 Internal Server Error** - LLM not configured:
```json
{
  "detail": "LLM client not configured"
}
```

**500 Internal Server Error** - Search or recommendation generation failed:
```json
{
  "detail": "Recommendation generation failed: [error details]"
}
```

## Workflow Details

### 1. Multimodal Search
- If text query provided: generates CLIP embedding
- If image provided: generates CLIP embedding from image
- Combines embeddings using weighted fusion: `fused = image_weight * image_emb + text_weight * text_emb`
- Searches Weaviate vector database for similar products

### 2. Context Building
- Retrieves user profile if available (preferences, purchase history)
- Analyzes preferences for colors, categories, style keywords
- Formats search results with rankings and relevance scores
- Builds comprehensive context for LLM

### 3. LLM Generation
- Sends formatted context + structured prompt to LLM
- Prompt requests 3 regular recommendations + 1 wildcard recommendation
- LLM returns JSON with product titles and explanations

### 4. Response Formatting
- Parses LLM JSON response
- Matches recommendations to search results
- Generates product links (`/products/{product_id}`)
- Adds product details for each recommendation
- Falls back to search results if LLM response is invalid JSON

## Recommendation Strategy

The endpoint generates 4 recommendations:
- **1st-3rd**: Personalized picks based on user preferences and search relevance
- **4th (Wildcard)**: Novel/unexpected item that still aligns with user style

This mix provides both familiar (expected preferences) and discovery (new ideas).

## Customization

### Adjust Search Weights
- `image_weight=0.8&text_weight=0.2`: Prioritize visual similarity
- `image_weight=0.5&text_weight=0.5`: Equal weighting
- `image_weight=0.3&text_weight=0.7`: Prioritize text relevance

### Control Results
- `top_k=3`: Consider only top 3 products for recommendations
- `top_k=10`: Consider more options (better diversity, slower)

## Integration Examples

### JavaScript/Fetch
```javascript
const formData = new FormData();
formData.append("user_id", "user123");
formData.append("query", "blue shirt");

const response = await fetch("/agent/recommend?top_k=5", {
  method: "POST",
  body: formData
});
const data = await response.json();
console.log(data.recommendations);
```

### Python/Requests
```python
import requests

files = {
    "user_id": (None, "user123"),
    "query": (None, "blue shirt")
}

response = requests.post(
    "http://localhost:8000/agent/recommend",
    files=files,
    params={"top_k": 5}
)

data = response.json()
for rec in data["recommendations"]:
    print(f"{rec['rank']}. {rec['title']}: {rec['description']}")
```

### With Image Upload
```python
files = {
    "user_id": (None, "user123"),
    "image": open("product.jpg", "rb")
}

response = requests.post(
    "http://localhost:8000/agent/recommend",
    files=files,
    params={"top_k": 5, "image_weight": 0.7}
)
```

## Performance Notes

- Response time typically 2-5 seconds (includes LLM API call)
- Multimodal search adds ~500ms vs text-only
- Image processing adds ~200-500ms depending on file size
- LLM generation is the main bottleneck (1-3s with OpenAI)

## Fallback Behavior

- If LLM response is invalid JSON: Uses search results as fallback recommendations
- If no user profile: Generates recommendations based on search results alone
- If LLM call fails: Returns error response with details
