# Debug Scoring Feature

## Overview

The debug scoring feature provides transparency into how search results are ranked by exposing the individual scoring components that contribute to the final ranking.

## How It Works

When `debug=true` is passed to any search endpoint, each result will include a `debug_scores` object with the following breakdown:

- **vector_score**: Cosine similarity between query and product embeddings (0.0-1.0)
- **color_score**: Bonus points for exact color match (0.0 or 0.2)
- **category_score**: Bonus points for exact category match (0.0 or 0.2)
- **text_score**: Similarity between query text and product title (0.0-0.1)
- **final_score**: Weighted combination of all scores

### Scoring Formula

```
final_score = (0.5 × vector_score) + (0.2 × color_score) + (0.2 × category_score) + (0.1 × text_score)
```

## API Usage

### Text Search with Debug

```bash
curl -X POST "http://localhost:8000/search/text" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "blue dress",
    "top_k": 5,
    "debug": true
  }'
```

**Response:**
```json
{
  "query": "blue dress",
  "results": [
    {
      "product_id": "prod_123",
      "title": "Elegant Blue Evening Dress",
      "category": "dresses",
      "color": "blue",
      "similarity": 0.8745,
      "distance": 0.1255,
      "debug_scores": {
        "vector_score": 0.8745,
        "color_score": 0.2,
        "category_score": 0.0,
        "text_score": 0.0856,
        "final_score": 0.6458
      }
    }
  ],
  "total_results": 1
}
```

### Image Search with Debug

```bash
curl -X POST "http://localhost:8000/search/image?debug=true&top_k=3" \
  -F "file=@product_image.jpg"
```

### Multimodal Search with Debug

```bash
curl -X POST "http://localhost:8000/search/multimodal?debug=true" \
  -F "text=red shoes" \
  -F "file=@shoe_image.jpg"
```

## Understanding the Scores

### Vector Score (Weight: 0.5)
- Primary ranking signal
- Measures semantic similarity between query and product
- Computed via cosine similarity of CLIP embeddings
- Higher values indicate better matches

### Color Score (Weight: 0.2)
- Binary boost: 0.2 if color exactly matches filter, 0.0 otherwise
- Only applies when color filter is provided
- Helps prioritize exact color matches

### Category Score (Weight: 0.2)
- Binary boost: 0.2 if category exactly matches filter, 0.0 otherwise
- Only applies when category filter is provided
- Helps prioritize products in the requested category

### Text Score (Weight: 0.1)
- Measures lexical overlap between query and product title
- Uses bag-of-words cosine similarity
- Maximum value: 0.1 (full match)
- Helps boost products with matching keywords

## Use Cases

### 1. Quality Assurance
Verify that ranking logic is working as expected:
```python
# Check if color filter is properly boosting results
response = search_text("blue shirt", color="blue", debug=True)
for result in response.results:
    assert result.debug_scores["color_score"] == 0.2
```

### 2. A/B Testing
Compare different scoring weights:
```python
# Test if text similarity is contributing effectively
results_with_text = search_text("running shoes", debug=True)
results_no_text = search_text("rnng shs", debug=True)
# Compare text_score differences
```

### 3. User Feedback
Explain to users why certain products ranked higher:
```
"This product ranked #1 because:
 - 87% semantic match with your query
 - Exact color match (+20%)
 - Contains matching keywords (+8%)"
```

### 4. Debugging
Identify issues in the ranking pipeline:
```python
# If top result has low final_score, investigate individual components
if result.debug_scores["final_score"] < 0.5:
    print(f"Low vector score: {result.debug_scores['vector_score']}")
    print(f"No filter boosts applied")
```

## Performance Note

Debug mode adds minimal overhead (~5ms per request) as all scores are computed during the ranking process. The debug flag only controls whether they are included in the response.

## Example Test Script

See `scripts/test_debug.py` for a complete testing suite that validates debug functionality across all search endpoints.

```python
# Run the test suite
python scripts/test_debug.py
```

## Disabling Debug Mode

By default, `debug=false`:
```json
{
  "query": "laptop",
  "top_k": 10
}
```

Results will not include `debug_scores` field, keeping responses compact.
