# Click Tracking & Analytics Quick Start

## Overview

The Click Tracking module records user interactions with search results, enabling comprehensive performance analysis across A/B test variants.

## Core Metrics Tracked

### 1. **Click-Through Rate (CTR)**
- Percentage of impressions that result in clicks
- Calculated per user, variant, and time period
- Formula: CTR = (Total Clicks / Total Impressions) × 100%

### 2. **Rank Metrics**
- Which result positions users click on
- Average, median, min, max rank clicked
- Distribution of clicks by rank position
- Identifies if users prefer top results or explore deeper

### 3. **Response Time**
- Latency of search operations
- Statistics: avg, min, max, 95th percentile
- Per-variant performance comparison
- Helps identify performance bottlenecks

## Quick Start

### 1. Log Search Impressions

When a user performs a search, log an impression:

```bash
curl -X POST http://localhost:8000/analytics/log-impression \
  -H "Content-Type: application/json" \
  -H "X-User-ID: user_123" \
  -d '{
    "query": "blue running shoes",
    "variant": "search_v1",
    "results_count": 42,
    "response_time_ms": 45.2
  }'
```

**Response:**
```json
{
  "status": "success",
  "user_id": "user_123",
  "query": "blue running shoes",
  "variant": "search_v1",
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

### 2. Log Click Events

When a user clicks on a result, log the click:

```bash
curl -X POST http://localhost:8000/analytics/log-click \
  -H "Content-Type: application/json" \
  -H "X-User-ID: user_123" \
  -d '{
    "product_id": "prod_nike_001",
    "rank": 2,
    "search_query": "blue running shoes",
    "variant": "search_v1",
    "response_time_ms": 45.2,
    "source": "SEARCH_RESULTS"
  }'
```

**Response:**
```json
{
  "status": "success",
  "user_id": "user_123",
  "product_id": "prod_nike_001",
  "rank": 2,
  "timestamp": "2024-01-15T10:30:50.234567"
}
```

### 3. Retrieve Metrics

#### Get Overall CTR
```bash
curl http://localhost:8000/analytics/ctr
```

#### Get CTR for Specific User
```bash
curl "http://localhost:8000/analytics/ctr?user_id=user_123"
```

#### Get CTR by Variant
```bash
curl "http://localhost:8000/analytics/ctr?variant=search_v1"
```

#### Get CTR for Last 30 Days
```bash
curl "http://localhost:8000/analytics/ctr?days=30"
```

**Response:**
```json
{
  "ctr": 0.25,
  "clicks": 10,
  "impressions": 40,
  "period_days": 7,
  "ctr_search_v1": 0.20,
  "ctr_search_v2": 0.30,
  "clicks_search_v1": 4,
  "clicks_search_v2": 6,
  "impressions_search_v1": 20,
  "impressions_search_v2": 20
}
```

### 4. Analyze Rank Metrics

```bash
curl http://localhost:8000/analytics/rank-metrics?user_id=user_123
```

**Response:**
```json
{
  "avg_rank": 2.5,
  "median_rank": 2,
  "min_rank": 0,
  "max_rank": 5,
  "clicks_by_rank": {
    "0": 3,
    "2": 2,
    "5": 1
  },
  "total_clicks": 6
}
```

### 5. Monitor Response Times

```bash
curl "http://localhost:8000/analytics/response-time?variant=search_v2"
```

**Response:**
```json
{
  "avg_response_time_ms": 58.5,
  "min_response_time_ms": 20.1,
  "max_response_time_ms": 150.3,
  "p95_response_time_ms": 120.0,
  "count": 100
}
```

### 6. Compare Variants

```bash
curl http://localhost:8000/analytics/variants-comparison?days=30
```

**Response:**
```json
{
  "period_days": 30,
  "variants": {
    "search_v1": {
      "ctr": 0.18,
      "avg_response_time_ms": 45.2,
      "avg_rank_clicked": 3.1,
      "total_clicks": 42,
      "total_impressions": 233
    },
    "search_v2": {
      "ctr": 0.25,
      "avg_response_time_ms": 52.1,
      "avg_rank_clicked": 2.8,
      "total_clicks": 58,
      "total_impressions": 232
    }
  },
  "winner_by_ctr": "search_v2"
}
```

### 7. Get User Summary

```bash
curl http://localhost:8000/analytics/user/user_123?days=7
```

**Response:**
```json
{
  "user_id": "user_123",
  "period_days": 7,
  "total_clicks": 15,
  "total_impressions": 50,
  "ctr": 0.30,
  "avg_rank_clicked": 2.3,
  "avg_response_time_ms": 48.5,
  "variants_used": ["search_v1", "search_v2"]
}
```

## Integration with A/B Testing

The Click Tracking module integrates seamlessly with the A/B Testing framework:

1. **Automatic Variant Tracking**: Each click is tagged with the variant that was used
2. **Per-Variant Metrics**: All endpoints support filtering by `variant` parameter
3. **Variant Comparison**: Built-in comparison endpoint shows V1 vs V2 performance

Example: Get metrics for search_v2 only:
```bash
curl "http://localhost:8000/analytics/ctr?variant=search_v2&days=30"
```

## Click Sources

The `source` field indicates where the click came from:

- `SEARCH_RESULTS` - User clicked a result in search results
- `RECOMMENDATIONS` - User clicked a recommended item
- `FEATURED` - User clicked a featured item
- `OTHER` - Other sources

## Time Range Filtering

All metrics endpoints support `days` parameter (1-365):

```bash
# Last 24 hours
curl "http://localhost:8000/analytics/ctr?days=1"

# Last 90 days
curl "http://localhost:8000/analytics/ctr?days=90"

# Last year
curl "http://localhost:8000/analytics/ctr?days=365"
```

Default: 7 days

## Query Parameters

### CTR Endpoint
- `user_id` (optional): Filter by specific user
- `variant` (optional): Filter by search variant (search_v1, search_v2)
- `days` (optional): Look-back period in days (1-365, default: 7)

### Rank Metrics Endpoint
- `user_id` (optional): Filter by specific user
- `variant` (optional): Filter by search variant
- `days` (optional): Look-back period in days

### Response Time Endpoint
- `user_id` (optional): Filter by specific user
- `variant` (optional): Filter by search variant
- `days` (optional): Look-back period in days

### User Analytics Endpoint
- Path parameter: `user_id` (required)
- `days` (optional): Look-back period in days

### Variant Comparison Endpoint
- `days` (optional): Look-back period in days

## MongoDB Storage

By default, metrics are stored in MongoDB:

**Database**: `omnisearch`
**Collections**:
- `click_events` - Records all click events
- `impressions` - Records all search impressions

**Indexes**:
- `user_id` - For filtering by user
- `variant` - For filtering by variant
- `timestamp` - For time-range queries
- Compound indexes for multi-field queries

If MongoDB is unavailable, the system gracefully degrades and returns default values.

## Demo Script

Run the comprehensive demo:

```bash
python scripts/demo_click_tracking.py
```

The demo shows:
1. Basic tracking workflow
2. Variant comparison with multiple searches
3. Rank position analysis
4. Response time analysis across variants
5. Comprehensive user summary

## API Endpoints Reference

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/analytics/log-click` | Log click event |
| POST | `/analytics/log-impression` | Log search impression |
| GET | `/analytics/ctr` | Get CTR metrics |
| GET | `/analytics/rank-metrics` | Analyze clicked rank positions |
| GET | `/analytics/response-time` | Get response time statistics |
| GET | `/analytics/user/{user_id}` | Get comprehensive user summary |
| GET | `/analytics/variants-comparison` | Compare V1 vs V2 performance |
| DELETE | `/analytics/reset` | Clear all tracking data |

## Troubleshooting

### No data returned
- Ensure you're logging impressions AND clicks
- Check time range with `days` parameter
- Verify variant names (search_v1, search_v2)

### MongoDB errors
- System works without MongoDB (in-memory fallback)
- Check MongoDB connection in logs
- Restart API server if needed

### Missing user metrics
- User ID must be provided via `X-User-ID` header or auto-generated
- Click and impression user IDs must match
- Check query parameters for typos

## Performance Considerations

- **Queries for large time ranges** (365 days) may take longer
- **MongoDB indexes** are automatically created for optimal performance
- **Per-user queries** are faster than global queries
- **Recent data** (last 7 days) is typically cached efficiently

## Next Steps

1. Review [CLICK_TRACKING.md](../docs/CLICK_TRACKING.md) for detailed documentation
2. Run the demo script to see all features in action
3. Integrate with your search endpoints
4. Monitor variant performance and make data-driven decisions
