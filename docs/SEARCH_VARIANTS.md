# Search Variants for A/B Testing

This document describes the two search variants implemented for A/B testing: **search_v1** (vector similarity only) and **search_v2** (vector + ranking engine).

## Overview

The search variants are designed to test different ranking approaches:

| Feature | V1 (Baseline) | V2 (Enhanced) |
|---------|---------------|---------------|
| **Algorithm** | Vector similarity only | Vector + multi-factor ranking |
| **Reranking** | Disabled | Enabled |
| **Speed** | Fast | Standard |
| **Best for** | Simple similarity retrieval | Comprehensive ranking |
| **Scoring Factors** | Vector similarity (1.0) | Vector (0.5) + Color (0.2) + Category (0.2) + Text (0.1) |

## Architecture

### Search Variants Module

Location: [`services/search_variants.py`](../../services/search_variants.py)

```
SearchVariantV1 (Vector Similarity Only)
├── search_by_text() → (ProductResult[], elapsed_ms)
├── search_by_image() → (ProductResult[], elapsed_ms)
└── Uses: enable_reranking=False

SearchVariantV2 (Vector + Ranking Engine)
├── search_by_text() → (ProductResult[], elapsed_ms)
├── search_by_image() → (ProductResult[], elapsed_ms)
└── Uses: enable_reranking=True
```

### API Integration

Location: [`api/ab_search.py`](../../api/ab_search.py)

Three new endpoints with A/B testing integration:

- **POST `/search-ab/text`** - Text search with variant assignment
- **POST `/search-ab/image`** - Image search with variant assignment
- **GET `/search-ab/variants`** - List available variants
- **GET `/search-ab/variant-info/{name}`** - Get variant details

All endpoints:
- Automatically assign user to variant via middleware
- Log search events to A/B framework
- Track timing and result counts
- Support filters (category, color)

## SearchVariantV1 (Vector Similarity Only)

### Behavior

```python
# Pure embedding-based search
results = SearchVariantV1.search_by_text("blue shoes")

# Uses ProductSearchService with:
# - enable_reranking=False
# - Returns results ranked by vector similarity only
# - No additional scoring factors applied
```

### Scoring Method

```
final_score = vector_similarity (0-1)
```

### Use Cases

- **Baseline comparison**: Measure improvement from V2
- **Speed-focused**: Minimal post-processing
- **Simple queries**: Direct semantic similarity
- **Resource-constrained**: Lower computational overhead

### Example Flow

```python
from services.search_variants import SearchVariantV1

# Execute V1 search
results, elapsed_ms = SearchVariantV1.search_by_text(
    query_text="blue running shoes",
    top_k=10,
    category_filter="footwear",
    color_filter="blue"
)

# Results ranked purely by vector similarity
# Faster execution, minimal features
```

## SearchVariantV2 (Vector + Ranking Engine)

### Behavior

```python
# Vector search + multi-factor ranking
results = SearchVariantV2.search_by_text("blue shoes")

# Uses ProductSearchService with:
# - enable_reranking=True
# - Applies scoring from ranking module
# - Considers multiple factors beyond vector similarity
```

### Scoring Method

```
final_score = 0.5*vector_sim + 0.2*color_match + 0.2*category_match + 0.1*text_sim
```

**Scoring Components:**

1. **Vector Similarity (0.5)** - Semantic similarity from embeddings
2. **Color Match (0.2)** - Exact color field match (1.0 if match, 0.0 if not)
3. **Category Match (0.2)** - Exact category field match (1.0 if match, 0.0 if not)
4. **Text Similarity (0.1)** - Cosine similarity between query and product title

### Use Cases

- **Comprehensive ranking**: Multiple ranking factors
- **Metadata utilization**: Leverages color/category fields
- **Quality focus**: Better ranking for user needs
- **Query understanding**: Text-title similarity helps intent matching

### Example Flow

```python
from services.search_variants import SearchVariantV2

# Execute V2 search
results, elapsed_ms = SearchVariantV2.search_by_text(
    query_text="blue running shoes",
    top_k=10,
    category_filter="footwear",
    color_filter="blue"
)

# Results ranked by multi-factor scoring:
# - Exact color matches boosted
# - Query text matches against titles
# - Semantic similarity + metadata features combined
# - Slower but more relevant results
```

## API Endpoints

### POST `/search-ab/text`

Search by text with A/B variant assignment.

**Parameters:**
- `query` (required) - Search query text
- `top_k` - Results to return (1-100, default 10)
- `category` - Optional category filter
- `color` - Optional color filter
- `debug` - Include scoring breakdown

**Response:**
```json
{
  "query": "blue shoes",
  "results": [
    {
      "product_id": "prod_001",
      "title": "Blue Running Shoes",
      "similarity": 0.95,
      ...
    }
  ],
  "total_results": 1
}
```

**Headers:**
- `X-User-ID` - User identifier (optional, auto-generated if missing)
- `X-Variant` - Assigned variant (response header)

**Example:**
```bash
curl -X POST "http://localhost:8000/search-ab/text?query=blue%20shoes&top_k=5" \
  -H "X-User-ID: user123"
```

### POST `/search-ab/image`

Search by image with A/B variant assignment.

**Parameters:**
- `file` (required) - Uploaded image file
- `top_k` - Results to return (1-100, default 10)
- `category` - Optional category filter
- `color` - Optional color filter

**Response:**
```json
{
  "filename": "shoes.jpg",
  "results": [...],
  "total_results": 5
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/search-ab/image?top_k=5" \
  -H "X-User-ID: user456" \
  -F "file=@shoes.jpg"
```

### GET `/search-ab/variants`

Get list of available search variants.

**Response:**
```json
{
  "variants": [
    {
      "name": "search_v1",
      "description": "Vector similarity only (baseline approach)"
    },
    {
      "name": "search_v2",
      "description": "Vector + ranking engine (enhanced with color/category/text scoring)"
    }
  ]
}
```

### GET `/search-ab/variant-info/{variant_name}`

Get detailed information about a specific variant.

**Response (for search_v1):**
```json
{
  "name": "search_v1",
  "type": "baseline",
  "description": "Vector similarity only",
  "scoring_factors": ["vector_similarity"],
  "reranking_enabled": false,
  "speed": "fast",
  "best_for": "Quick, simple similarity-based retrieval"
}
```

**Response (for search_v2):**
```json
{
  "name": "search_v2",
  "type": "enhanced",
  "description": "Vector + multi-factor ranking",
  "scoring_factors": [
    "vector_similarity (0.5)",
    "color_match (0.2)",
    "category_match (0.2)",
    "text_similarity (0.1)"
  ],
  "reranking_enabled": true,
  "speed": "standard",
  "best_for": "Comprehensive ranking with semantic and metadata matching"
}
```

## Integration with A/B Framework

### Automatic Variant Assignment

The middleware automatically:
1. Extracts or generates user ID
2. Assigns variant (50/50 split by default)
3. Injects variant into request context
4. Returns variant in response headers

```python
# Middleware extracts user from:
# 1. X-User-ID header
# 2. user_id cookie
# 3. Auto-generated UUID
```

### Event Logging

Each search automatically logs:
- User ID
- Assigned variant
- Query text
- Result count
- Search time (ms)
- Session ID (optional)

```python
# Automatically called by endpoints
manager.log_search(
    user_id="user123",
    query="blue shoes",
    results_count=10,
    search_time_ms=45.2,
    session_id="session_456"
)
```

### Metrics Collection

Available via `/ab/metrics` endpoint:

```json
{
  "total_searches": 100,
  "searches_by_variant": {
    "search_v1": 50,
    "search_v2": 50
  },
  "avg_results_by_variant": {
    "search_v1": 9.8,
    "search_v2": 9.9
  },
  "avg_response_time_by_variant": {
    "search_v1": 42.5,
    "search_v2": 48.3
  },
  "ctr_by_variant": {
    "search_v1": 0.15,
    "search_v2": 0.18
  }
}
```

## Implementation Details

### Service Integration

Both variants use the existing `ProductSearchService`:

```python
class SearchVariantV1:
    @staticmethod
    def search_by_text(query_text, top_k=10, ...):
        service = get_search_service()
        results = service.search_by_text(
            query_text=query_text,
            top_k=top_k,
            enable_reranking=False,  # V1 difference
            ...
        )
        return results, elapsed_ms

class SearchVariantV2:
    @staticmethod
    def search_by_text(query_text, top_k=10, ...):
        service = get_search_service()
        results = service.search_by_text(
            query_text=query_text,
            top_k=top_k,
            enable_reranking=True,  # V2 difference
            ...
        )
        return results, elapsed_ms
```

### Ranking Module

V2 uses the ranking module for re-ranking:

```python
# From services/ranking.py
rerank_results(
    results=vector_search_results,
    query_text=query,
    query_color=color_filter,
    query_category=category_filter,
    add_score_field=True,
    add_debug_scores=enable_debug
)
```

### Response Format

Both variants return `ProductResult` objects:

```python
ProductResult(
    product_id="prod_001",
    title="Blue Running Shoes",
    description="...",
    color="blue",
    category="footwear",
    image_path="/images/shoes.jpg",
    similarity=0.95,  # V1: vector similarity, V2: final_score
    distance=0.05,    # Weaviate distance metric
    debug_scores=None # Optional scoring breakdown
)
```

## Testing

### Unit Tests

Location: [`tests/test_search_variants.py`](../../tests/test_search_variants.py)

Tests cover:
- V1 vector similarity-only behavior
- V2 re-ranking behavior
- Filter application
- Error handling
- Result conversion

### Integration Tests

Location: [`tests/test_search_ab_integration.py`](../../tests/test_search_ab_integration.py)

Tests cover:
- Variant assignment
- Search execution
- Event logging
- Metrics collection
- Variant consistency

### Running Tests

```bash
# Run all variant tests
pytest tests/test_search_variants.py -v

# Run integration tests
pytest tests/test_search_ab_integration.py -v

# Run both with coverage
pytest tests/test_search_variants.py tests/test_search_ab_integration.py --cov=services.search_variants
```

## Demo Script

Location: [`scripts/demo_search_variants.py`](../../scripts/demo_search_variants.py)

Run the demo:

```bash
python scripts/demo_search_variants.py
```

Demos included:
1. **Basic Assignment** - Assign users to variants
2. **Variant Comparison** - Show differences in behavior
3. **Search and Logging** - Execute searches and log events
4. **Metrics** - View A/B comparison metrics
5. **Consistency** - Verify consistent assignment

## Performance Characteristics

### V1 (Vector Similarity Only)

- **Vector search**: ~40-50ms
- **Post-processing**: None
- **Total time**: 40-50ms
- **Memory**: Minimal
- **Ranking quality**: Good for simple queries

### V2 (Vector + Ranking)

- **Vector search**: ~40-50ms
- **Re-ranking**: ~5-10ms (fetches 30 results, ranks to top_k)
- **Total time**: 45-60ms
- **Memory**: Slightly higher (holds more temporary results)
- **Ranking quality**: Better for complex queries

## Best Practices

### When to Use V1

- Simple semantic matching
- Speed-critical scenarios
- Baseline for comparisons
- Resource-constrained environments
- Direct similarity queries

### When to Use V2

- Important search accuracy
- Metadata-rich products
- Complex user intent
- Quality-focused applications
- Queries mentioning colors/categories

### Testing Recommendations

1. **Duration**: Run for at least 1-2 weeks to get statistically significant results
2. **Sample Size**: Aim for 100+ searches per variant minimum
3. **Metrics**: Compare CTR, time-to-interaction, conversion
4. **Segment**: Test separately for different query types
5. **Statistical Test**: Use chi-square test for CTR significance

### Monitoring

Monitor these metrics for each variant:

- **Search volume**: Searches per variant over time
- **Performance**: Average response time per variant
- **Results**: Average result count per variant
- **Engagement**: Click-through rate (if click tracking enabled)
- **Quality**: User satisfaction (if surveys enabled)

## Troubleshooting

### V1 not disabling re-ranking

Check that `SearchVariantV1.search_by_text()` passes `enable_reranking=False`:

```python
# Verify in services/search_variants.py
results = search_service.search_by_text(
    ...
    enable_reranking=False,  # Must be False for V1
    ...
)
```

### V2 not applying ranking factors

Verify that ranking module is being called:

```python
# Check that enable_reranking=True is passed
# And that all required filter parameters are passed
```

### Timing seems off

Timing is measured around service call only:

```python
# Includes: Vector search + re-ranking (if enabled)
# Excludes: Network latency, serialization
```

### Results differ between variants

This is expected! V2 re-ranking changes order. Check:
- Are both using same `top_k`?
- Are filters applied correctly?
- Is re-ranking module being called?

## Future Enhancements

Potential improvements:

1. **Custom weights** - Allow configuring ranking weights per query type
2. **Embedding models** - Test different CLIP models
3. **Ranking algorithms** - Add ML-based ranking
4. **A/A testing** - Verify metrics consistency
5. **Multi-armed bandit** - Dynamic variant allocation based on performance
6. **Statistical significance** - Automated significance testing
