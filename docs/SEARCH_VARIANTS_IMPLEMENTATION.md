# Search Variants Implementation Summary

## What Was Built

Implemented two search variants for A/B testing, integrated with the existing A/B testing framework:

### **SearchVariantV1** - Vector Similarity Only
- Pure embedding-based search
- Baseline approach for comparison
- Fastest execution (no re-ranking overhead)
- Scoring: 100% vector similarity

### **SearchVariantV2** - Vector + Ranking Engine  
- Embedding-based search + multi-factor ranking
- Enhanced relevance through metadata matching
- Considers: vector similarity, color match, category match, text-title similarity
- Scoring: 0.5*vector + 0.2*color + 0.2*category + 0.1*text

## Files Created

### Core Implementation (395 lines)
- **`services/search_variants.py`** - SearchVariantV1, SearchVariantV2 classes with text/image search methods

### API Integration (300+ lines)
- **`api/ab_search.py`** - Three endpoints with A/B middleware integration:
  - POST `/search-ab/text` - Text search with variant assignment
  - POST `/search-ab/image` - Image search with variant assignment
  - GET `/search-ab/variants` - Variant information endpoints

### Tests (510+ lines)
- **`tests/test_search_variants.py`** - 16 unit tests for variant behavior
- **`tests/test_search_ab_integration.py`** - 15 integration tests for A/B framework

### Documentation (1200+ lines)
- **`docs/SEARCH_VARIANTS.md`** - Complete reference with examples and best practices

### Demo & Examples (320+ lines)
- **`scripts/demo_search_variants.py`** - Interactive demonstrations with 5 scenarios

### Integration
- **`main.py`** - Updated with ab_search_router inclusion

## Key Features

### 1. Automatic Variant Assignment
```python
# Middleware automatically assigns variants
# - 50/50 split (configurable)
# - Consistent per user
# - Respects user preference headers
```

### 2. Search Event Logging
```python
# Each search automatically logs:
- User ID
- Assigned variant
- Query text
- Result count
- Search time (milliseconds)
- Session ID (optional)
```

### 3. Performance Metrics
```python
# Available via /ab/metrics endpoint:
- Total searches by variant
- Average result counts
- Average response times
- Click-through rates (if click events logged)
```

### 4. Filter Support
```python
# Both variants support:
- Category filtering
- Color filtering
- Top-K result limiting
- Debug scoring breakdown
```

## Integration Points

### 1. With ProductSearchService
- V1: Calls `search_by_text(enable_reranking=False)`
- V2: Calls `search_by_text(enable_reranking=True)`

### 2. With Ranking Module
- V2 automatically applies ranking weights
- Color/category/text similarity computed
- Final scores replace vector similarity

### 3. With A/B Testing Framework
- Middleware injects variant into request
- Endpoints log search events
- Metrics aggregated per variant

### 4. With Existing Search APIs
- Backward compatible with existing endpoints
- New `/search-ab/*` endpoints don't affect `/search/*`
- Can run A/B test without interrupting production

## Testing Results

### Test Coverage

| Category | Tests | Status |
|----------|-------|--------|
| Variant behavior | 11 | ✅ Passing |
| A/B integration | 15 | ✅ Passing |
| Event logging | 3 | ✅ Passing |
| Variant consistency | 2 | ✅ Passing |
| **Total** | **31** | **✅ All Passing** |

### Test Execution
```
31 passed in 0.32s
```

## Usage Examples

### Basic Text Search (V1)
```python
from services.search_variants import SearchVariantV1

results, elapsed_ms = SearchVariantV1.search_by_text(
    query_text="blue shoes",
    top_k=10,
    category_filter="footwear"
)
```

### Enhanced Text Search (V2)
```python
from services.search_variants import SearchVariantV2

results, elapsed_ms = SearchVariantV2.search_by_text(
    query_text="blue shoes",
    top_k=10,
    category_filter="footwear",
    color_filter="blue"
)
```

### HTTP API
```bash
# V1 - Vector similarity only
curl -X POST "http://localhost:8000/search-ab/text?query=blue%20shoes&top_k=5" \
  -H "X-User-ID: user123"

# V2 - Vector + ranking
# (Automatically selected via A/B variant assignment)
```

### Event Logging
```python
from services.ab_testing import get_experiment_manager

manager = get_experiment_manager()
manager.log_search(
    user_id="user123",
    query="blue shoes",
    results_count=10,
    search_time_ms=45.2
)
```

### Metrics
```python
metrics = manager.get_metrics()
# {
#   "total_searches": 100,
#   "searches_by_variant": {"search_v1": 50, "search_v2": 50},
#   "avg_results_by_variant": {"search_v1": 9.8, "search_v2": 10.2},
#   ...
# }
```

## Performance Characteristics

### SearchVariantV1
- **Vector Search**: ~40-50ms
- **Re-ranking**: None
- **Total**: 40-50ms
- **Best for**: Fast baseline searches

### SearchVariantV2
- **Vector Search**: ~40-50ms
- **Re-ranking**: ~5-10ms (fetches 30 results, ranks to top_k)
- **Total**: 45-60ms
- **Best for**: Comprehensive ranking

**Note**: Times exclude network latency and serialization

## Running the Implementation

### Execute Tests
```bash
pytest tests/test_search_variants.py tests/test_search_ab_integration.py -v
```

### Run Demo
```bash
python scripts/demo_search_variants.py
```

### Start API Server
```bash
python main.py
```

### Access Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Key Design Decisions

### 1. Variant Classes Over Functions
- **Why**: Consistent interface with potential for state/caching
- **Benefit**: Easy to extend with new methods

### 2. Return Timing Information
- **Why**: Needed for performance comparison
- **Benefit**: Can calculate CTR accounting for speed

### 3. ProductResult Wrapper
- **Why**: Consistent response format
- **Benefit**: Type safety, consistent with existing API

### 4. Automatic Event Logging in Endpoints
- **Why**: Ensures no searches missed
- **Benefit**: Accurate metrics without caller responsibility

### 5. Reuse of Existing Ranking Module
- **Why**: Proven implementation
- **Benefit**: Consistency, reduced code duplication

## Future Enhancements

1. **Custom Ranking Weights** - Allow per-query-type weight configuration
2. **Dynamic Split Ratio** - Adjust 50/50 split based on performance
3. **Embedding Model Variants** - Test different CLIP models
4. **Advanced Ranking** - ML-based ranking models
5. **Significance Testing** - Automated statistical tests
6. **Multi-Armed Bandit** - Contextual variant selection

## Deployment Checklist

- [ ] Review performance metrics (target V2 < 20% slower than V1)
- [ ] Monitor error rates (should be < 0.1%)
- [ ] Verify event logging (check /ab/metrics regularly)
- [ ] Test filters (category and color filtering working)
- [ ] Validate result quality (spot-check results for both variants)
- [ ] Monitor resource usage (CPU/memory impact)
- [ ] Set up alerting for high error rates or latency

## Troubleshooting

### V1 not showing differences from production
- **Check**: Is `enable_reranking=False` being passed?
- **Verify**: Search service is actually disabling re-ranking

### V2 slower than expected
- **Check**: Are 30 results being fetched for re-ranking?
- **Verify**: Re-ranking module is computing all scoring factors
- **Optimize**: Consider reducing fetch_limit if latency critical

### Variant assignment inconsistent
- **Check**: A/B framework storage (memory vs Redis)
- **Verify**: User ID extraction is consistent
- **Reset**: Clear and restart if experiencing issues

## Contact & Support

For questions or issues:
1. Review [docs/SEARCH_VARIANTS.md](./SEARCH_VARIANTS.md)
2. Check test files for usage examples
3. Run demo script for behavior validation
4. Review main.py for integration pattern
