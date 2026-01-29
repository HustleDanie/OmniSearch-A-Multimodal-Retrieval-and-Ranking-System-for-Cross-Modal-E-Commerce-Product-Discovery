# A/B Testing Quick Integration Guide

Step-by-step instructions to integrate A/B testing into your search endpoints.

## 1. Install Dependencies (if needed)

A/B testing uses only standard FastAPI and Python libraries. No additional packages required.

Optional for Redis:
```bash
pip install redis
```

## 2. Middleware is Already Integrated

The middleware is automatically enabled in `main.py`:

```python
# main.py already includes:
from api.ab_middleware import ABTestingMiddleware
from api.ab_endpoints import router as ab_router

app.add_middleware(ABTestingMiddleware)  # ✓ Already added
app.include_router(ab_router)             # ✓ Already added
```

No action needed here.

## 3. Add Logging to Your Search Endpoint

### Example: Text Search Endpoint

Before:
```python
@app.get("/search/text")
async def search_text(query: str):
    results = weaviate_client.search(query)
    return {"results": results}
```

After:
```python
from fastapi import Depends
from api.ab_middleware import get_user_id, get_session_id
from services.ab_testing import get_experiment_manager
import time

@app.get("/search/text")
async def search_text(
    query: str,
    user_id: str = Depends(get_user_id),
    session_id: str = Depends(get_session_id)
):
    manager = get_experiment_manager()
    
    # Perform search
    start_time = time.time()
    results = weaviate_client.search(query)
    search_time_ms = (time.time() - start_time) * 1000
    
    # Log to A/B test
    manager.log_search(
        user_id=user_id,
        query=query,
        results_count=len(results),
        search_time_ms=search_time_ms,
        session_id=session_id
    )
    
    return {
        "results": results,
        "count": len(results),
        "variant": manager.get_assignment(user_id).variant.value
    }
```

## 4. Add Click Tracking

Create a new endpoint for click events:

```python
from pydantic import BaseModel

class ClickRequest(BaseModel):
    product_id: str
    product_title: str = ""
    position: int = -1
    query: str = ""

@app.post("/click")
async def handle_click(
    click: ClickRequest,
    user_id: str = Depends(get_user_id),
    session_id: str = Depends(get_session_id)
):
    manager = get_experiment_manager()
    
    # Log the click
    manager.log_click(
        user_id=user_id,
        product_id=click.product_id,
        product_title=click.product_title,
        position=click.position,
        query=click.query,
        session_id=session_id
    )
    
    # You can also integrate with your tracking system here
    # e.g., update_user_memory(user_id, product)
    
    return {"success": True}
```

## 5. Test the Integration

### Start the server:
```bash
uvicorn main:app --reload
```

### Test in another terminal:

```bash
# 1. Assign variant
curl -X POST "http://localhost:8000/ab/assign?user_id=test_user"

# 2. Perform search
curl "http://localhost:8000/search/text?query=shoes" \
  -H "X-User-ID: test_user" \
  -H "X-Session-ID: session_123"

# 3. Log a click
curl -X POST "http://localhost:8000/click" \
  -H "X-User-ID: test_user" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "prod_456",
    "product_title": "Running Shoes",
    "position": 0,
    "query": "shoes"
  }'

# 4. View metrics
curl "http://localhost:8000/ab/metrics"
```

## 6. Run the Demo

Interactive demonstration with simulated data:

```bash
python scripts/demo_ab_testing.py
```

This will:
- Assign 5 users to variants
- Simulate search and click flow
- Simulate 20 users with random interactions
- Show aggregate metrics
- Query and filter events
- Reset and clean up

## 7. Variant-Specific Logic (Optional)

If you want different search algorithms for each variant:

```python
from api.ab_middleware import inject_variant

@app.get("/search/smart")
async def smart_search(
    query: str,
    variant: str = Depends(inject_variant)
):
    if variant == "search_v1":
        # Original algorithm
        results = search_bm25(query)
    else:  # search_v2
        # New algorithm
        results = search_with_ml_ranking(query)
    
    return {"results": results, "variant": variant}
```

## 8. Monitor Results

### Via API:
```bash
# Get current metrics
curl "http://localhost:8000/ab/metrics" | jq

# Get variant for user
curl "http://localhost:8000/ab/assignment?user_id=user123"

# Query events
curl "http://localhost:8000/ab/events?variant=search_v1&limit=50"
```

### Via Python:
```python
from services.ab_testing import get_experiment_manager

manager = get_experiment_manager()

# Get metrics
metrics = manager.get_metrics()
print(f"V1 CTR: {metrics['search_v1']['ctr']:.2%}")
print(f"V2 CTR: {metrics['search_v2']['ctr']:.2%}")

# Get events for analysis
events = manager.get_events(event_type="click", limit=100)
for event in events:
    print(f"{event.user_id} clicked {event.product_id}")
```

## 9. Configuration

Set these environment variables to customize behavior:

```env
# Default: memory (fast, loses on restart)
# Options: memory, redis, file
AB_STORAGE=memory

# Default: 0.5 (50/50 split)
# Range: 0.0-1.0 (probability for variant 1)
AB_SPLIT_RATIO=0.5

# Default: ab_events.jsonl
# Path to JSONL event log
AB_LOG_FILE=ab_events.jsonl

# For Redis backend
REDIS_URL=redis://localhost:6379/0
```

## 10. Production Checklist

Before deploying to production:

- [ ] Verify test coverage: `pytest tests/test_ab_*.py -v`
- [ ] Add click tracking to main endpoints
- [ ] Configure AB_STORAGE (use Redis for production)
- [ ] Set up log file location (AB_LOG_FILE)
- [ ] Configure monitoring for /ab/metrics
- [ ] Document experiment hypothesis
- [ ] Plan experiment duration (minimum 1-2 weeks)
- [ ] Plan sample size (target ≥1000 searches per variant)
- [ ] Schedule metric reviews (daily or weekly)
- [ ] Plan variant rollout based on results

## Common Integration Patterns

### Pattern 1: Multiple Search Endpoints

Apply the same logging pattern to all search endpoints:

```python
async def log_search_helper(user_id, query, results, search_time_ms, session_id):
    manager = get_experiment_manager()
    manager.log_search(user_id, query, len(results), search_time_ms, session_id)

@app.get("/search/text")
async def search_text(...):
    # ... search logic ...
    await log_search_helper(user_id, query, results, time_ms, session_id)

@app.get("/search/image")
async def search_image(...):
    # ... search logic ...
    await log_search_helper(user_id, query, results, time_ms, session_id)
```

### Pattern 2: Combine with update_user_memory

Log click and update user profile:

```python
from db.user_service import UserProfileService

@app.post("/click")
async def handle_click(
    product_id: str,
    product_title: str,
    user_id: str = Depends(get_user_id),
    session_id: str = Depends(get_session_id)
):
    ab_manager = get_experiment_manager()
    user_service = UserProfileService()
    
    # Log click for A/B test
    ab_manager.log_click(user_id, product_id, product_title, session_id=session_id)
    
    # Update user profile
    product = {"title": product_title, "product_id": product_id}
    user_service.update_user_memory(user_id, product)
    
    return {"success": True}
```

### Pattern 3: Automatic Experiment Winner Selection

After sufficient data, automatically use better variant:

```python
def get_best_variant():
    manager = get_experiment_manager()
    metrics = manager.get_metrics()
    
    v1_ctr = metrics["search_v1"]["ctr"]
    v2_ctr = metrics["search_v2"]["ctr"]
    
    # Need sufficient data
    if metrics["search_events"] < 1000:
        return None  # Not enough data
    
    # Return winner with 5% improvement threshold
    if v1_ctr > v2_ctr * 1.05:
        return "search_v1"
    elif v2_ctr > v1_ctr * 1.05:
        return "search_v2"
    
    return None  # No clear winner
```

## Troubleshooting Integration

### Issue: User ID not consistent
**Solution**: Always pass `X-User-ID` header in client code:
```python
headers = {"X-User-ID": user.id}
requests.get("/search/text?query=shoes", headers=headers)
```

### Issue: Events not showing in metrics
**Solution**: Verify events are being logged:
```bash
curl "http://localhost:8000/ab/metrics"
# Check that total_events > 0
```

### Issue: Click tracking not working
**Solution**: Verify click endpoint is being called:
```python
# Add logging
import logging
logger = logging.getLogger(__name__)

@app.post("/click")
async def handle_click(...):
    logger.info(f"Click event: {product_id}")  # Check logs
```

### Issue: Different search time measurements
**Solution**: Time the operation consistently:
```python
import time

start = time.time()
results = perform_search(query)
elapsed_ms = (time.time() - start) * 1000

manager.log_search(..., search_time_ms=elapsed_ms)
```

## Next Steps

1. **Read full docs**: [docs/AB_TESTING.md](../docs/AB_TESTING.md)
2. **Run tests**: `pytest tests/test_ab_testing.py tests/test_ab_endpoints.py -v`
3. **Run demo**: `python scripts/demo_ab_testing.py`
4. **Implement**: Add logging to your endpoints (copy examples above)
5. **Monitor**: Check `/ab/metrics` regularly
6. **Analyze**: After 1-2 weeks, determine variant winner
7. **Decide**: Roll out winner or run next experiment

## Support

- **API Docs**: `http://localhost:8000/docs` (when running)
- **Tests**: Review `tests/test_ab_testing.py` for examples
- **Demo**: Run `scripts/demo_ab_testing.py` for hands-on examples
- **Documentation**: See [docs/AB_TESTING.md](../docs/AB_TESTING.md) for complete reference
