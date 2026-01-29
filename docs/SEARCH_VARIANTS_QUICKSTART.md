# Search Variants Quick Start

## What Are Search Variants?

Two different search algorithms for A/B testing:

- **V1**: Vector similarity only (fast baseline)
- **V2**: Vector + ranking engine (comprehensive ranking)

## Start Using Them

### 1. Run the Server
```bash
python main.py
```

### 2. Make a Search Request
```bash
# Automatically gets assigned to either V1 or V2
curl -X POST "http://localhost:8000/search-ab/text?query=blue%20shoes" \
  -H "X-User-ID: user123"
```

### 3. Check Your Variant
```bash
# See what variant you were assigned
curl -X GET "http://localhost:8000/ab/assignment" \
  -H "X-User-ID: user123"
```

### 4. View Results
```bash
# Check aggregate metrics
curl http://localhost:8000/ab/metrics
```

## Key Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /search-ab/text` | Search with variant |
| `POST /search-ab/image` | Image search with variant |
| `GET /search-ab/variants` | List variants |
| `GET /ab/metrics` | View A/B metrics |
| `GET /ab/assignment` | Check your variant |

## In Code

### Direct Variant Usage
```python
from services.search_variants import SearchVariantV1, SearchVariantV2

# V1 - Vector only
results_v1, time_v1 = SearchVariantV1.search_by_text("blue shoes")

# V2 - Vector + ranking
results_v2, time_v2 = SearchVariantV2.search_by_text("blue shoes")
```

### With A/B Framework
```python
from services.ab_testing import get_experiment_manager
from services.search_variants import get_search_variant

manager = get_experiment_manager()

# Assign user to variant
assignment = manager.assign_variant("user123")

# Get the assigned variant
variant = get_search_variant("search_v1")

# Execute search
results, elapsed_ms = variant.search_by_text("blue shoes")

# Log event
manager.log_search("user123", "blue shoes", len(results), elapsed_ms)

# View metrics
metrics = manager.get_metrics()
```

## Run Demo

```bash
python scripts/demo_search_variants.py
```

Shows:
- How variants are assigned
- How they behave differently
- How events are logged
- What metrics look like

## Run Tests

```bash
pytest tests/test_search_variants.py tests/test_search_ab_integration.py -v
```

All 31 tests should pass ✅

## Understand the Difference

### V1 (Baseline)
```
Results ranked by: vector_similarity (0-1)
Speed: Fast (~45ms)
Use case: Simple similarity matching
```

### V2 (Enhanced)  
```
Results ranked by:
  - vector_similarity (50%)
  - color_match (20%)
  - category_match (20%)
  - text_similarity (10%)
Speed: Standard (~50ms)
Use case: Better relevance with metadata
```

## Typical A/B Test Flow

1. **Day 1-7**: Run test, collect baseline metrics
2. **Day 8-14**: Analyze results, check significance
3. **Week 3+**: Expand to more users if winner is clear
4. **Month 1+**: Make decision to keep V1/V2 or iterate

## Key Metrics to Watch

- **Search Count**: Total searches per variant (should be balanced)
- **Response Time**: V2 might be 5-15ms slower (acceptable)
- **Click-Through Rate**: V2 should have higher CTR if working well
- **User Engagement**: V2 might lead to more interactions

## Next Steps

1. ✅ Run the server (`python main.py`)
2. ✅ Make some searches to `/search-ab/text`
3. ✅ Check metrics with `/ab/metrics`
4. ✅ Read [docs/SEARCH_VARIANTS.md](./SEARCH_VARIANTS.md) for details
5. ✅ Review [docs/SEARCH_VARIANTS_IMPLEMENTATION.md](./SEARCH_VARIANTS_IMPLEMENTATION.md) for architecture

## Troubleshooting

**Q: Both variants returning same results?**
A: V1 only returns vector similarity, V2 re-ranks. Order might look similar if color/category match doesn't help much.

**Q: V2 timing seems same as V1?**
A: Timing includes only search execution. Network/serialization overhead is similar for both.

**Q: How to control 50/50 split?**
A: Edit `ExperimentManager.assign_variant()` in `services/ab_testing.py` and adjust `split_ratio` parameter.

**Q: How to persist assignments between restarts?**
A: Configure Redis backend in `ExperimentManager.__init__()` instead of memory dict.

## Questions?

- API Docs: http://localhost:8000/docs
- Swagger: http://localhost:8000/docs#/
- Code: Check `services/search_variants.py` and `api/ab_search.py`
