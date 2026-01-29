# Quick Start: POST /agent/recommend

## API Endpoint

```
POST /agent/recommend
```

## Minimal Example

### Request (Text Query)
```bash
curl -X POST http://localhost:8000/agent/recommend \
  -F "user_id=user123" \
  -F "query=blue casual shirt"
```

### Response
```json
{
  "user_id": "user123",
  "query": "blue casual shirt",
  "image_filename": null,
  "recommendations": [
    {
      "rank": 1,
      "title": "Blue Casual Shirt",
      "description": "Perfect match for your query...",
      "is_wildcard": false,
      "product_link": "/products/PROD-001",
      "product_details": {...}
    },
    {
      "rank": 2,
      "title": "Light Blue Oxford",
      "description": "Similar style with premium fabric...",
      "is_wildcard": false,
      "product_link": "/products/PROD-002",
      "product_details": {...}
    },
    {
      "rank": 3,
      "title": "Navy Dress Shirt",
      "description": "Versatile option for formal occasions...",
      "is_wildcard": false,
      "product_link": "/products/PROD-003",
      "product_details": {...}
    },
    {
      "rank": 4,
      "title": "Vintage Denim Overshirt",
      "description": "A wildcard suggestion for added style diversity...",
      "is_wildcard": true,
      "product_link": "/products/PROD-004",
      "product_details": {...}
    }
  ],
  "search_results_count": 5,
  "llm_prompt_summary": "You are a fashion/product stylist..."
}
```

## Common Use Cases

### 1. Get Recommendations for User
```bash
curl -X POST http://localhost:8000/agent/recommend \
  -F "user_id=user_john" \
  -F "query=summer dresses" \
  -G -d "top_k=5"
```

### 2. Search by Image
```bash
curl -X POST http://localhost:8000/agent/recommend \
  -F "user_id=user_jane" \
  -F "image=@/path/to/product.jpg" \
  -G -d "top_k=5"
```

### 3. Multimodal (Text + Image)
```bash
curl -X POST http://localhost:8000/agent/recommend \
  -F "user_id=user_bob" \
  -F "query=casual" \
  -F "image=@/path/to/style.jpg" \
  -G -d "top_k=5&image_weight=0.7&text_weight=0.3"
```

### 4. Prioritize Text Over Image
```bash
curl -X POST http://localhost:8000/agent/recommend \
  -F "user_id=user_alice" \
  -F "query=professional blazer" \
  -F "image=@/path/to/reference.jpg" \
  -G -d "image_weight=0.3&text_weight=0.7"
```

### 5. Request More Candidates
```bash
curl -X POST http://localhost:8000/agent/recommend \
  -F "user_id=user_charlie" \
  -F "query=winter coats" \
  -G -d "top_k=10"
```

## Parameter Reference

| Parameter | Type | Required | Default | Range | Notes |
|-----------|------|----------|---------|-------|-------|
| user_id | string | ✓ | - | - | Unique user identifier |
| query | string | * | - | - | Text search (required if no image) |
| image | file | * | - | - | Image file (required if no query) |
| top_k | int | ✗ | 5 | 1-20 | Products to consider for recs |
| image_weight | float | ✗ | 0.6 | 0-1.0 | Image search importance |
| text_weight | float | ✗ | 0.4 | 0-1.0 | Text search importance |

\* At least one required

## Response Format

```typescript
{
  user_id: string                    // Echo of input user_id
  query: string | null              // Echo of input query
  image_filename: string | null     // Name of uploaded image
  recommendations: [                 // Array of 1-4 recommendations
    {
      rank: number                  // 1-4 (position)
      title: string                 // Product name
      description: string           // Why recommended
      is_wildcard: boolean          // Novel suggestion
      product_link: string | null   // API link to product
      product_details: object | null // Full product info
    }
  ]
  search_results_count: number      // Products evaluated
  llm_prompt_summary: string        // LLM prompt preview
}
```

## Error Responses

### Missing Query and Image
```
400 Bad Request
{
  "detail": "Provide at least one of: query text or image file"
}
```

### Invalid File Type
```
400 Bad Request
{
  "detail": "File must be an image"
}
```

### LLM Not Configured
```
500 Internal Server Error
{
  "detail": "LLM client not configured"
}
```

### Server Error
```
500 Internal Server Error
{
  "detail": "Recommendation generation failed: [error details]"
}
```

## Integration Examples

### JavaScript/Fetch
```javascript
// Text query
const formData = new FormData();
formData.append('user_id', 'user123');
formData.append('query', 'blue shirt');

const response = await fetch('/agent/recommend?top_k=5', {
  method: 'POST',
  body: formData
});

const recommendations = await response.json();
recommendations.recommendations.forEach(rec => {
  console.log(`${rec.rank}. ${rec.title}`);
  console.log(`   ${rec.description}`);
});
```

### Python/Requests
```python
import requests

# Text query
response = requests.post(
    'http://localhost:8000/agent/recommend',
    files={'user_id': (None, 'user123'), 'query': (None, 'blue shirt')},
    params={'top_k': 5}
)

data = response.json()
for rec in data['recommendations']:
    print(f"{rec['rank']}. {rec['title']}")
    print(f"   {rec['description']}")

# With image
with open('product.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/agent/recommend',
        files={
            'user_id': (None, 'user123'),
            'image': f
        },
        params={'top_k': 5}
    )
```

### React/TypeScript
```typescript
interface Recommendation {
  rank: number;
  title: string;
  description: string;
  is_wildcard: boolean;
  product_link: string | null;
}

interface RecommendResponse {
  user_id: string;
  recommendations: Recommendation[];
  search_results_count: number;
}

async function getRecommendations(
  userId: string,
  query: string
): Promise<RecommendResponse> {
  const formData = new FormData();
  formData.append('user_id', userId);
  formData.append('query', query);

  const response = await fetch('/agent/recommend?top_k=5', {
    method: 'POST',
    body: formData
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  return await response.json();
}
```

## Best Practices

1. **Always provide user_id** - For personalization and tracking
2. **Use meaningful queries** - Specific queries produce better results
3. **Balance weights** - Default 0.6/0.4 works well for most cases
4. **Control top_k** - Higher values = more search but slower
5. **Handle errors** - Check HTTP status code and error message
6. **Cache results** - Same query/user may return same recommendations
7. **Use product_links** - Generated links work with product endpoints

## Testing

### With curl
```bash
# Test endpoint is working
curl http://localhost:8000/agent/recommend \
  -F "user_id=test" \
  -F "query=test"

# Expected: 200 OK with recommendations
```

### With Python
```python
import requests

response = requests.post(
    'http://localhost:8000/agent/recommend',
    files={'user_id': (None, 'test'), 'query': (None, 'test')}
)
print(f"Status: {response.status_code}")
print(f"Recs: {len(response.json()['recommendations'])}")
```

## What Gets Returned

1. **Recommendations** - AI-selected products with explanations
2. **Product Links** - `/products/{product_id}` for follow-up
3. **Full Details** - Color, category, price, similarity scores
4. **Metadata** - How many products were evaluated
5. **Transparency** - LLM prompt summary for debugging

## Performance

- **Typical Response Time**: 2-5 seconds
- **Bottleneck**: LLM API call (1-3s)
- **Image Processing**: 200-500ms
- **Search**: 300-500ms
- **Recommendations**: Up to 4 items

## Configuration

Set these environment variables:

```bash
# For OpenAI integration
OPENAI_API_KEY=sk-your-key-here
LLM_PROVIDER=openai
LLM_MODEL=gpt-3.5-turbo

# Or leave blank for mock mode (demo/testing)
```

## Next Steps

1. Start the server: `python main.py`
2. Try the endpoint: See examples above
3. Check `/docs` for interactive API docs
4. Run tests: `pytest tests/test_agent_endpoint.py -v`
5. Read full docs: See `docs/ENDPOINT_RECOMMEND.md`
