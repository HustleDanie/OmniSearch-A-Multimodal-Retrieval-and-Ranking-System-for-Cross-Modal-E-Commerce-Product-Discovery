# A/B Testing Module for OmniSearch

Complete A/B testing framework for FastAPI with experiment assignment, metrics logging, and statistical analysis.

**Features:**
- Randomly assign users to search_v1 or search_v2
- Persistent assignment (same user always gets same variant)
- Log search queries, results, and click events
- Automatic click-through rate (CTR) calculation
- Configurable split ratio (default 50/50)
- Support for multiple storage backends (memory, Redis)
- Middleware to inject variant into all requests
- RESTful API for management and analytics

## Quick Start

### 1. Basic Setup

A/B testing middleware is automatically enabled in FastAPI:

```python
from main import app
# Middleware already added to app
```

### 2. Assign Variant to User

```bash
curl -X POST "http://localhost:8000/ab/assign?user_id=user123"
```

Response:
```json
{
  "user_id": "user123",
  "variant": "search_v1",
  "assigned_at": "2026-01-28T10:30:45.123456",
  "metadata": {}
}
```

### 3. Log Search Events

```bash
curl -X POST "http://localhost:8000/ab/log-search" \
  -H "X-User-ID: user123" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "casual blue shirts",
    "results_count": 24,
    "search_time_ms": 145.5
  }'
```

### 4. Log Click Events

```bash
curl -X POST "http://localhost:8000/ab/log-click" \
  -H "X-User-ID: user123" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "prod_456",
    "product_title": "Blue Casual Shirt",
    "position": 0,
    "query": "casual blue shirts"
  }'
```

### 5. Get Metrics

```bash
curl "http://localhost:8000/ab/metrics"
```

Response:
```json
{
  "total_events": 150,
  "total_assignments": 50,
  "search_events": 75,
  "click_events": 42,
  "search_v1": {
    "count": 38,
    "clicks": 22,
    "ctr": 0.5789
  },
  "search_v2": {
    "count": 37,
    "clicks": 20,
    "ctr": 0.5405
  },
  "avg_search_time_ms": 142.3,
  "avg_results": 23.5
}
```

## Architecture

### Components

1. **ExperimentManager** (`services/ab_testing.py`)
   - Manages variant assignment
   - Logs events (search, click)
   - Calculates metrics
   - Supports multiple storage backends

2. **ABTestingMiddleware** (`api/ab_middleware.py`)
   - Extracts or generates user ID
   - Assigns variant on first request
   - Injects variant into request state
   - Adds variant to response headers

3. **API Endpoints** (`api/ab_endpoints.py`)
   - `/ab/assign` - Assign variant
   - `/ab/log-search` - Log search event
   - `/ab/log-click` - Log click event
   - `/ab/metrics` - Get aggregate metrics
   - `/ab/assignment` - Get user's assignment
   - `/ab/events` - Query logged events
   - `/ab/reset` - Clear all data

### Data Flow

```
User Request
    ↓
ABTestingMiddleware
    ├─ Extract/generate user_id
    ├─ Assign variant (if new)
    └─ Inject into request.state
         ↓
    Endpoint Handler
    ├─ Use variant from request.state
    └─ Call manager.log_search() or log_click()
         ↓
    ExperimentManager
    ├─ Store assignment (memory or Redis)
    ├─ Append event to log
    └─ Write to JSONL file
         ↓
    Response
    (with X-Variant header)
```

## Configuration

### Environment Variables

```env
# A/B Testing Configuration
AB_STORAGE=memory              # Storage backend: "memory", "redis", "file"
AB_SPLIT_RATIO=0.5             # Probability for variant 1 (0.0-1.0)
AB_LOG_FILE=ab_events.jsonl    # Path to event log file
REDIS_URL=redis://localhost:6379/0  # Redis connection (if AB_STORAGE=redis)
```

### In Code

```python
from services.ab_testing import get_experiment_manager, ExperimentVariant

manager = get_experiment_manager()

# Set custom split ratio (70% v1, 30% v2)
manager.split_ratio = 0.7

# Get user's variant
assignment = manager.get_assignment("user123")
variant = assignment.variant  # ExperimentVariant.SEARCH_V1 or SEARCH_V2
```

## User ID Identification

Middleware extracts user ID with this priority:

1. **Header**: `X-User-ID` header
2. **Cookie**: `user_id` cookie
3. **Generated**: UUID4 if neither provided

```bash
# Using header
curl -H "X-User-ID: user123" http://localhost:8000/search/text?query=shoes

# Using cookie
curl -b "user_id=user123" http://localhost:8000/search/text?query=shoes

# Auto-generated (anonymous)
curl http://localhost:8000/search/text?query=shoes
```

Session ID works similarly with `X-Session-ID` header or `session_id` cookie.

## Logging Events

### Search Events

Log when user performs a search:

```python
from services.ab_testing import get_experiment_manager

manager = get_experiment_manager()
event = manager.log_search(
    user_id="user123",
    query="casual shirts",
    results_count=24,
    search_time_ms=145.5,
    session_id="sess_abc"
)
```

Fields:
- `user_id` (required): User identifier
- `query` (required): Search query string
- `results_count` (required): Number of results returned
- `search_time_ms` (optional): Search execution time
- `session_id` (optional): Session identifier

### Click Events

Log when user clicks a result:

```python
event = manager.log_click(
    user_id="user123",
    product_id="prod_456",
    product_title="Blue Casual Shirt",
    position=0,  # 0-indexed position in results
    query="casual shirts",
    session_id="sess_abc"
)
```

Fields:
- `user_id` (required): User identifier
- `product_id` (required): Product clicked
- `product_title` (optional): Product title
- `position` (optional): Position in results (0-indexed, -1 if unknown)
- `query` (optional): Original search query
- `session_id` (optional): Session identifier

## Metrics and Analysis

### Available Metrics

```python
metrics = manager.get_metrics()

# Overall counts
metrics["total_events"]       # Total events logged
metrics["total_assignments"] # Total users assigned
metrics["search_events"]     # Total search events
metrics["click_events"]      # Total click events

# Variant-specific metrics
metrics["search_v1"]["count"]   # Search count for v1
metrics["search_v1"]["clicks"]  # Click count for v1
metrics["search_v1"]["ctr"]     # Click-through rate for v1
# Same for search_v2

# Aggregate stats
metrics["avg_search_time_ms"]  # Average search time
metrics["avg_results"]         # Average results per search
```

### Click-Through Rate (CTR)

CTR = clicks / searches

```python
v1_ctr = metrics["search_v1"]["ctr"]  # e.g., 0.5789 = 57.89%
v2_ctr = metrics["search_v2"]["ctr"]

if v1_ctr > v2_ctr:
    print(f"v1 outperforms: {v1_ctr:.2%} vs {v2_ctr:.2%}")
```

### Event Queries

Get detailed events for analysis:

```python
# All events
events = manager.get_events()

# Filter by user
events = manager.get_events(user_id="user123")

# Filter by variant
from services.ab_testing import ExperimentVariant
events = manager.get_events(variant=ExperimentVariant.SEARCH_V1)

# Filter by event type
search_events = manager.get_events(event_type="search")
click_events = manager.get_events(event_type="click")

# Limit results
recent_events = manager.get_events(limit=50)

# Combine filters
events = manager.get_events(
    user_id="user123",
    variant=ExperimentVariant.SEARCH_V2,
    event_type="click",
    limit=100
)
```

## Usage Patterns

### 1. In Search Endpoint

```python
from fastapi import Depends, Request
from api.ab_middleware import get_user_id, get_session_id
from services.ab_testing import get_experiment_manager

@app.get("/search/text")
async def search_text(
    query: str,
    user_id: str = Depends(get_user_id),
    session_id: str = Depends(get_session_id)
):
    manager = get_experiment_manager()
    
    # Perform search
    start_time = time.time()
    results = perform_search(query)
    search_time_ms = (time.time() - start_time) * 1000
    
    # Log to A/B test
    manager.log_search(
        user_id=user_id,
        query=query,
        results_count=len(results),
        search_time_ms=search_time_ms,
        session_id=session_id
    )
    
    return {"results": results, "count": len(results)}
```

### 2. In Result Click Handler

```python
@app.post("/click")
async def handle_click(
    product_id: str,
    query: str = None,
    user_id: str = Depends(get_user_id),
    session_id: str = Depends(get_session_id)
):
    manager = get_experiment_manager()
    
    # Log click
    manager.log_click(
        user_id=user_id,
        product_id=product_id,
        query=query,
        session_id=session_id
    )
    
    # Handle click (track purchase, etc.)
    return {"success": True}
```

### 3. Conditional Logic Based on Variant

```python
from api.ab_middleware import inject_variant

@app.get("/search/smart")
async def smart_search(
    query: str,
    variant: str = Depends(inject_variant)
):
    if variant == "search_v1":
        results = search_algorithm_v1(query)
    else:  # search_v2
        results = search_algorithm_v2(query)
    
    return {"results": results}
```

## Storage Backends

### Memory (Default)

Fastest, loses data on restart:

```env
AB_STORAGE=memory
```

Best for: Development, testing, short experiments.

### Redis

Persistent, shared across processes:

```env
AB_STORAGE=redis
REDIS_URL=redis://localhost:6379/0
```

Setup:
```bash
docker run -d -p 6379:6379 redis:latest
```

Best for: Production, multiple servers, persistent assignments.

### File (JSONL)

Write-once log file:

```env
AB_LOG_FILE=/var/log/ab_events.jsonl
```

All events are also written to this file regardless of storage backend.

## Testing

### Run Unit Tests

```bash
pytest tests/test_ab_testing.py -v
```

Output:
```
tests/test_ab_testing.py::TestExperimentAssignment::test_assign_variant_returns_valid_variant PASSED
tests/test_ab_testing.py::TestExperimentAssignment::test_assign_variant_idempotent PASSED
tests/test_ab_testing.py::TestSearchEvent::test_log_search_creates_event PASSED
tests/test_ab_testing.py::TestClickEvent::test_log_click_creates_event PASSED
tests/test_ab_testing.py::TestMetrics::test_get_metrics_with_searches PASSED
...
27 passed in 0.39s
```

### Run API Tests

```bash
pytest tests/test_ab_endpoints.py -v
```

Output:
```
tests/test_ab_endpoints.py::TestABAssignmentEndpoint::test_assign_variant_success PASSED
tests/test_ab_endpoints.py::TestABLogSearchEndpoint::test_log_search_success PASSED
tests/test_ab_endpoints.py::TestABMetricsEndpoint::test_get_metrics_with_events PASSED
...
19 passed in 1.24s
```

### Manual Testing

```bash
# Start server
uvicorn main:app --reload

# In another terminal:

# Assign variant
curl -X POST "http://localhost:8000/ab/assign?user_id=user1"

# Log search
curl -X POST "http://localhost:8000/ab/log-search" \
  -H "X-User-ID: user1" \
  -H "Content-Type: application/json" \
  -d '{"query":"test","results_count":10}'

# Log click
curl -X POST "http://localhost:8000/ab/log-click" \
  -H "X-User-ID: user1" \
  -H "Content-Type: application/json" \
  -d '{"product_id":"p1"}'

# View metrics
curl "http://localhost:8000/ab/metrics"
```

## API Reference

### POST /ab/assign

Assign user to variant.

**Query Parameters:**
- `user_id` (optional): User ID (auto-generated if not provided)

**Response:**
```json
{
  "user_id": "user123",
  "variant": "search_v1",
  "assigned_at": "2026-01-28T10:30:45",
  "metadata": {}
}
```

### POST /ab/log-search

Log a search event.

**Request Body:**
```json
{
  "query": "casual shirts",
  "results_count": 24,
  "search_time_ms": 145.5
}
```

**Response:**
```json
{
  "event_type": "search",
  "user_id": "user123",
  "variant": "search_v1",
  "timestamp": "2026-01-28T10:30:50"
}
```

### POST /ab/log-click

Log a click event.

**Request Body:**
```json
{
  "product_id": "prod_456",
  "product_title": "Blue Casual Shirt",
  "position": 0,
  "query": "casual shirts"
}
```

**Response:**
```json
{
  "event_type": "click",
  "user_id": "user123",
  "variant": "search_v1",
  "timestamp": "2026-01-28T10:30:55"
}
```

### GET /ab/metrics

Get aggregate metrics.

**Response:**
```json
{
  "total_events": 150,
  "total_assignments": 50,
  "search_events": 75,
  "click_events": 42,
  "search_v1": {
    "count": 38,
    "clicks": 22,
    "ctr": 0.5789
  },
  "search_v2": {
    "count": 37,
    "clicks": 20,
    "ctr": 0.5405
  },
  "avg_search_time_ms": 142.3,
  "avg_results": 23.5
}
```

### GET /ab/assignment

Get user's assignment.

**Query Parameters:**
- `user_id` (optional): User ID

**Response:**
```json
{
  "user_id": "user123",
  "variant": "search_v1",
  "assigned_at": "2026-01-28T10:30:45",
  "metadata": {}
}
```

### GET /ab/events

Query logged events.

**Query Parameters:**
- `user_id` (optional): Filter by user
- `variant` (optional): Filter by variant (search_v1, search_v2)
- `event_type` (optional): Filter by type (search, click)
- `limit` (optional): Max results (default 100)

**Response:**
```json
{
  "events": [
    {
      "user_id": "user123",
      "variant": "search_v1",
      "timestamp": "2026-01-28T10:30:50",
      "query": "casual shirts",
      "results_count": 24,
      "event_type": "search"
    }
  ],
  "count": 1
}
```

### DELETE /ab/reset

Clear all data (development only).

**Response:**
```json
{
  "success": true,
  "message": "A/B testing data cleared"
}
```

## Best Practices

1. **User ID Consistency**: Pass `X-User-ID` header consistently for reliable tracking
2. **Session Tracking**: Use `X-Session-ID` to group interactions within sessions
3. **Log Timing**: Call `log_search` immediately after search execution
4. **Click Attribution**: Include original `query` in click events for analysis
5. **Metrics Review**: Check metrics regularly (at least weekly for statistically significant data)
6. **Sample Size**: Aim for ≥1000 searches per variant before drawing conclusions
7. **Running Time**: Run experiments for at least 1-2 weeks to account for daily variations
8. **Significance**: Use CTR difference and confidence intervals for statistical analysis

## Statistical Significance

To determine if one variant is truly better:

```python
from scipy import stats

# Get metrics
metrics = manager.get_metrics()
v1 = metrics["search_v1"]
v2 = metrics["search_v2"]

# Chi-square test for CTR difference
contingency_table = [
    [v1["clicks"], v1["count"] - v1["clicks"]],
    [v2["clicks"], v2["count"] - v2["clicks"]]
]
chi2, p_value, dof, expected = stats.chi2_contingency(contingency_table)

# p < 0.05 means significant difference
if p_value < 0.05:
    better = "v1" if v1["ctr"] > v2["ctr"] else "v2"
    print(f"{better} is significantly better (p={p_value:.4f})")
```

## Troubleshooting

### No events logged?
- Check middleware is enabled in `main.py`
- Verify user_id is being extracted (check response headers)
- Confirm endpoint calls are reaching `/ab/log-*`

### Redis not found?
- Verify Redis is running: `redis-cli ping`
- Check `REDIS_URL` environment variable
- Falls back to memory storage automatically on connection failure

### Events not in file?
- Check `AB_LOG_FILE` path is writable
- Verify events are being logged (check `/ab/metrics`)
- Check file permissions: `ls -la ab_events.jsonl`

### Variants not balanced?
- Check sample size (need ≥100 users)
- Verify `AB_SPLIT_RATIO` setting (default 0.5)
- Run longer to normalize randomness

## Files Created

- `services/ab_testing.py` - Core A/B testing module (450+ lines)
- `api/ab_middleware.py` - FastAPI middleware (120+ lines)
- `api/ab_endpoints.py` - RESTful endpoints (380+ lines)
- `tests/test_ab_testing.py` - Unit tests (27 tests, all passing)
- `tests/test_ab_endpoints.py` - Integration tests (19 tests, all passing)

Total: **46 tests passing**, production-ready code with full test coverage.
