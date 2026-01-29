# Experimentation System

## Overview

OmniSearch includes a comprehensive A/B testing framework for comparing search algorithm variants and tracking their impact on user behavior. The system supports:

- **Multi-variant experiments** - Compare multiple search strategies simultaneously
- **User assignment** - Consistent user-to-variant mapping
- **Event tracking** - Capture search, click, and impression events
- **Metrics calculation** - Compute CTR, dwell time, revenue impact
- **Analysis** - Statistical significance testing and performance reports

---

## Architecture

```
┌─────────────────────────────────────────┐
│         API Endpoints                   │
│  /search/text, /search/image            │
└────────────────┬────────────────────────┘
                 │
        ┌────────▼────────┐
        │ A/B Testing     │
        │ Middleware      │
        └────────┬────────┘
                 │
    ┌────────────┴────────────┐
    │                         │
┌───▼────┐          ┌────────▼────┐
│ Assign │          │ Track Event │
│ User   │          │ (Search,    │
│ Variant│          │  Click,     │
└────────┘          │  Impression)│
                    └─────────────┘
    │                    │
    └────────┬───────────┘
             │
    ┌────────▼──────────┐
    │  MongoDB Storage  │
    │  - Assignments    │
    │  - Events         │
    │  - Metrics        │
    └───────────────────┘
```

---

## Core Components

### 1. ExperimentVariant (Enum)

```python
class ExperimentVariant(str, Enum):
    SEARCH_V1 = "search_v1"  # Baseline search
    SEARCH_V2 = "search_v2"  # Improved search with ranking
```

**Available variants:**
- `SEARCH_V1` - Baseline vector similarity search
- `SEARCH_V2` - Enhanced with re-ranking and filters

**Adding new variants:**
1. Add to `ExperimentVariant` enum
2. Implement search logic in `SearchService`
3. Update routing in API

### 2. ExperimentAssignment

Represents a user's persistent assignment to a variant.

```python
@dataclass
class ExperimentAssignment:
    user_id: str                          # Unique user ID
    variant: ExperimentVariant            # Assigned variant
    assigned_at: datetime                 # Assignment timestamp
    metadata: Dict[str, Any]              # Custom metadata
```

**Key features:**
- Persistent assignment per user
- Timestamp tracking for analysis
- Metadata for custom attributes

### 3. Event Tracking Classes

#### SearchEvent
```python
@dataclass
class SearchEvent(ExperimentEvent):
    results_count: int                    # Number of results returned
    search_time_ms: float                 # Query execution time
    event_type: str = "search"            # Event identifier
```

#### ClickEvent
```python
@dataclass
class ClickEvent(ExperimentEvent):
    product_id: str                       # Clicked product
    product_title: str                    # Product name
    position: int                         # Position in results (1-indexed)
    event_type: str = "click"
```

#### ImpressionEvent
```python
@dataclass
class ImpressionEvent(ExperimentEvent):
    product_id: str                       # Shown product
    position: int                         # Position in results
    visible: bool = True                  # Viewport visibility
    event_type: str = "impression"
```

---

## Usage

### 1. Assign User to Variant

```python
from services.ab_testing import ABTestingService, ExperimentVariant

ab_service = ABTestingService()

# Assign user to variant
assignment = ab_service.assign_user(user_id="user_123")
print(assignment.variant)  # SEARCH_V1 or SEARCH_V2
```

**Assignment strategy:**
- Consistent: Same user always gets same variant (using hash-based bucketing)
- Random: 50/50 split between variants
- Weighted: Custom split percentages

### 2. Track Search Event

```python
from services.ab_testing import SearchEvent

# Get user's assigned variant
assignment = ab_service.get_assignment("user_123")

# Track search
event = SearchEvent(
    user_id="user_123",
    variant=assignment.variant,
    query="blue shoes",
    results_count=42,
    search_time_ms=145.3,
    session_id="session_456"
)

ab_service.track_event(event)
```

### 3. Track Click Event

```python
from services.ab_testing import ClickEvent

# User clicks on product at position 3
event = ClickEvent(
    user_id="user_123",
    variant=assignment.variant,
    product_id="product_789",
    product_title="Blue Running Shoes",
    position=3,
    session_id="session_456"
)

ab_service.track_event(event)
```

### 4. Calculate Metrics

```python
# CTR by variant
metrics = ab_service.calculate_ctr(
    start_date="2026-01-01",
    end_date="2026-01-31",
    variant_filter="search_v2"
)

print(metrics)
# Output:
# {
#   "ctr": 0.15,
#   "clicks": 450,
#   "impressions": 3000,
#   "by_position": {
#     "1": 0.45,
#     "2": 0.28,
#     "3": 0.15
#   }
# }
```

### 5. Statistical Analysis

```python
# Compare variants statistically
stats = ab_service.compare_variants(
    variant1="search_v1",
    variant2="search_v2",
    metric="ctr",
    confidence_level=0.95
)

print(stats)
# Output:
# {
#   "v1_value": 0.12,
#   "v2_value": 0.18,
#   "difference": 0.06,
#   "p_value": 0.0234,
#   "significant": True,
#   "confidence_interval": [0.01, 0.11]
# }
```

---

## Data Storage

### MongoDB Collections

#### assignments
```json
{
  "_id": ObjectId(),
  "user_id": "user_123",
  "variant": "search_v2",
  "assigned_at": ISODate("2026-01-28T10:00:00Z"),
  "metadata": {}
}
```

**Indexes:**
- `user_id` (unique) - Fast user lookup
- `variant` - Filter by variant
- `assigned_at` - Time-based queries

#### events
```json
{
  "_id": ObjectId(),
  "user_id": "user_123",
  "variant": "search_v2",
  "event_type": "search",
  "timestamp": ISODate("2026-01-28T10:15:30Z"),
  "query": "blue shoes",
  "session_id": "session_456",
  "results_count": 42,
  "search_time_ms": 145.3,
  "metadata": {}
}
```

**Indexes:**
- `user_id` - User history
- `variant` - Variant filtering
- `event_type` - Event classification
- `[variant, timestamp]` - Time-series queries
- `[event_type, timestamp]` - Event-based aggregation

---

## Experiment Lifecycle

### Phase 1: Design
1. Define hypothesis: "Re-ranking improves CTR"
2. Select metrics: CTR, dwell time, conversion
3. Determine sample size: N = 5000 users
4. Set duration: 2 weeks

### Phase 2: Setup
```python
# Create experiment
experiment = ab_service.create_experiment(
    name="ranking_improvement_v2",
    hypothesis="Re-ranking improves CTR",
    variant_a="search_v1",
    variant_b="search_v2",
    sample_size=5000,
    duration_days=14
)
```

### Phase 3: Running
- Users assigned to variants
- Events tracked in real-time
- Metrics calculated daily
- Alerts on statistical significance

### Phase 4: Analysis
```python
# Generate report
report = ab_service.generate_report(
    experiment_id="ranking_improvement_v2",
    include_visualizations=True
)

print(report)
# Output:
# Experiment: ranking_improvement_v2
# Duration: 2026-01-28 to 2026-02-11
# 
# Results:
# - Variant V1: CTR=12.3%, N=2510
# - Variant V2: CTR=18.7%, N=2490
# - Difference: +6.4% (p=0.0012) ✓ SIGNIFICANT
# 
# Recommendation: Deploy Variant V2
```

### Phase 5: Decision
- **Winner detected** - Deploy variant
- **No difference** - Keep baseline or extend
- **Loser detected** - Roll back immediately

---

## Best Practices

### 1. Sample Size
**Rule of thumb:** Minimum 100 events per variant per metric

```python
# Calculate required sample size
from scipy.stats import norm

effect_size = 0.05      # 5% improvement
alpha = 0.05            # Type I error (5%)
beta = 0.20             # Type II error (20%)

z_alpha = norm.ppf(1 - alpha/2)
z_beta = norm.ppf(1 - beta)

n_per_variant = ((z_alpha + z_beta) / effect_size) ** 2
# For 5% effect: ~3,100 users per variant
```

### 2. Duration
- **Minimum:** 1 week (capture weekly patterns)
- **Typical:** 2-4 weeks (account for seasonality)
- **Maximum:** 8 weeks (diminishing returns)

### 3. Metrics Selection
- **Primary metric:** CTR (required)
- **Secondary metrics:** Dwell time, conversion, revenue
- **Guardrail metrics:** Latency, error rate

### 4. Variant Naming
```python
# Good: Descriptive and version-controlled
"search_v1_baseline"
"ranking_v2_improved"
"filters_v3_nested"

# Bad: Vague or conflicting
"test1"
"new_search"
"variant_a"
```

### 5. Event Quality
```python
# Always include:
- user_id (consistent)
- variant (assigned)
- timestamp (accurate)
- session_id (aggregation)

# Common issues:
- Duplicate events (idempotency)
- Missing user_id (anonymization)
- Wrong timestamp (server time)
```

---

## Common Patterns

### Pattern 1: Gradual Rollout

```python
# Start with 10% traffic
experiment = ab_service.create_experiment(
    name="ranking_v2_rollout",
    variant_a="search_v1",
    variant_b="search_v2",
    traffic_split=0.10,  # 10% to V2
    enable_ramp_up=True,
    ramp_up_schedule=[0.10, 0.25, 0.50, 1.00]
)

# Day 1-3: 10% traffic
# Day 4-6: 25% traffic
# Day 7-9: 50% traffic
# Day 10+: 100% traffic
```

### Pattern 2: Holdout Group

```python
# Always keep 5% on baseline for comparison
experiment = ab_service.create_experiment(
    name="ranking_v2_with_holdout",
    variant_a="search_v1",
    variant_b="search_v2",
    holdout_percent=0.05,  # Keep 5% on V1
)
```

### Pattern 3: Time-Series Analysis

```python
# Track metrics over time
daily_metrics = ab_service.get_metrics_by_day(
    experiment_id="ranking_v2",
    metric="ctr"
)

# Plot: CTR progression
# Day 1: V1=12%, V2=12% (no difference initially)
# Day 3: V1=12%, V2=15% (trend emerging)
# Day 7: V1=12%, V2=18% (significant)
```

---

## Troubleshooting

### Issue: Variant Assignment Not Consistent

**Problem:** Same user gets different variants on different requests

**Solution:**
```python
# Ensure hash-based assignment
assignment = ab_service.get_assignment(user_id)
if not assignment:
    # First time: assign based on hash
    bucket = hash(user_id) % 100
    variant = "v1" if bucket < 50 else "v2"
    assignment = ab_service.assign_user(user_id, variant)
```

### Issue: Low Event Volume

**Problem:** Events not being tracked

**Solution:**
```python
# Verify event tracking
event = SearchEvent(user_id="test_user", variant="search_v1", ...)
ab_service.track_event(event)

# Check database
events = ab_service.get_user_events("test_user")
assert len(events) > 0, "Events not persisted"
```

### Issue: Metrics Not Calculating

**Problem:** CTR returns 0 or None

**Solution:**
```python
# Verify data exists
event_count = ab_service.count_events(
    variant="search_v2",
    start_date="2026-01-28"
)
print(f"Events: {event_count}")

# Verify clicks and impressions
clicks = ab_service.count_events(
    variant="search_v2",
    event_type="click"
)
impressions = ab_service.count_events(
    variant="search_v2",
    event_type="impression"
)
print(f"CTR: {clicks}/{impressions} = {clicks/impressions:.2%}")
```

---

## Performance

### Query Performance

| Query | Time | Notes |
|-------|------|-------|
| Get assignment (cached) | <1ms | User lookup |
| Track event | 2-5ms | Single insert |
| Calculate CTR | 50-200ms | Aggregation over time range |
| Compare variants | 200-500ms | Multiple aggregations |
| Generate report | 1-5s | All metrics + analysis |

### Scaling

- **10K users:** Single MongoDB instance sufficient
- **100K users:** Add read replicas for metrics queries
- **1M users:** Partition by time range, archive old data
- **10M users:** Dedicated metrics cluster + streaming pipeline

---

## Integration Points

### 1. Search API
```python
@router.post("/search/text")
async def search_by_text(request: TextSearchRequest):
    # Get user assignment
    assignment = ab_service.get_assignment(request.user_id)
    
    # Route to variant
    if assignment.variant == ExperimentVariant.SEARCH_V1:
        results = search_v1(request)
    else:
        results = search_v2(request)
    
    # Track event
    ab_service.track_event(SearchEvent(
        user_id=request.user_id,
        variant=assignment.variant,
        query=request.query,
        results_count=len(results),
        session_id=request.session_id
    ))
    
    return results
```

### 2. Click Tracking
```python
@router.post("/track/click")
async def track_click(click_data: ClickRequest):
    # Get user's variant
    assignment = ab_service.get_assignment(click_data.user_id)
    
    # Track click
    ab_service.track_event(ClickEvent(
        user_id=click_data.user_id,
        variant=assignment.variant,
        product_id=click_data.product_id,
        position=click_data.position,
        session_id=click_data.session_id
    ))
    
    return {"status": "tracked"}
```

### 3. Analytics Dashboard
```python
# Fetch metrics for display
metrics = ab_service.get_daily_metrics(
    start_date="2026-01-15",
    end_date="2026-01-31"
)

# Returns:
# {
#   "search_v1": {"ctr": 0.12, "avg_time": 145.3, ...},
#   "search_v2": {"ctr": 0.18, "avg_time": 156.2, ...}
# }
```

---

## Advanced Topics

### Multivariate Testing

Test multiple factors simultaneously:

```python
experiment = ab_service.create_experiment(
    name="multivariate_search",
    factors={
        "ranking": ["baseline", "improved"],
        "filters": ["simple", "advanced"],
        "display": ["list", "grid"]
    }
)

# Creates 2 × 2 × 2 = 8 combinations
# Each user sees one combination
```

### Sequential Testing

Stop early when significance is reached:

```python
def should_stop_experiment(experiment_id):
    stats = ab_service.get_stats(experiment_id)
    
    # Stop if significant at p < 0.05
    if stats["p_value"] < 0.05:
        return True
    
    # Stop if enough data and no effect
    if stats["n_per_variant"] > 5000 and abs(stats["effect"]) < 0.01:
        return True
    
    return False
```

### Cohort Analysis

Segment users by characteristics:

```python
# Compare variants by user segment
cohorts = ab_service.get_metrics_by_cohort(
    experiment_id="ranking_v2",
    cohort_field="country"
)

# Output:
# {
#   "US": {"v1_ctr": 0.12, "v2_ctr": 0.19, "difference": 0.07},
#   "UK": {"v1_ctr": 0.11, "v2_ctr": 0.16, "difference": 0.05},
#   "DE": {"v1_ctr": 0.13, "v2_ctr": 0.17, "difference": 0.04}
# }
```

---

## References

- [A/B Testing Guide](https://www.optimizely.com/ab-testing/)
- [Statistical Significance](https://en.wikipedia.org/wiki/Statistical_hypothesis_testing)
- [Sample Size Calculator](https://www.statsignificance.com/)
- [Experimentation Platform Patterns](https://netflix.techblog.com/scaling-testing-at-netflix-5e74f02649a0)

---

**Status**: ✅ Complete
**Last Updated**: January 28, 2026
