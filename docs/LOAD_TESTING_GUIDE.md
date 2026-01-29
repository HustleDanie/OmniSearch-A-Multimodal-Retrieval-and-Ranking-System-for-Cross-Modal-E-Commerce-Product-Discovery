# OmniSearch Load Testing Guide

## Overview

Two load testing tools for measuring search endpoint performance under concurrent load:

1. **AsyncIO** - Programmatic, fast, lightweight (no UI)
2. **Locust** - Interactive UI, real-time monitoring, detailed reports

---

## Quick Start

### AsyncIO Load Test (Command Line)

```bash
# Basic test: 100 users, 10 requests each
python scripts/load_test_asyncio.py

# Custom parameters
python scripts/load_test_asyncio.py \
  --url http://localhost:8000 \
  --users 100 \
  --requests 10 \
  --export results/load_test.json

# High load: 500 users
python scripts/load_test_asyncio.py --users 500 --requests 20
```

### Locust Load Test (Interactive UI)

```bash
# Install locust first
pip install locust

# Start locust web interface
locust -f scripts/load_test_locust.py \
  --host=http://localhost:8000 \
  --users=100 \
  --spawn-rate=10

# Then open browser to: http://localhost:8089
```

---

## Tool Comparison

| Feature | AsyncIO | Locust |
|---------|---------|--------|
| **Setup** | No dependencies | Requires pip install |
| **UI** | Command line | Web dashboard |
| **Real-time Monitoring** | No | Yes |
| **Export** | JSON | HTML + JSON |
| **Scripting** | Python direct | Python tasks |
| **Flexibility** | High | Medium |
| **Learning Curve** | Steep | Gentle |
| **Best For** | CI/CD automation | Manual testing |

---

## AsyncIO Load Test

### Features

- ✅ 100+ concurrent users
- ✅ Configurable requests per user
- ✅ Detailed latency metrics (min, max, avg, p50, p95, p99)
- ✅ Error tracking and reporting
- ✅ JSON export for analysis
- ✅ No external dependencies (uses Python stdlib)

### Command Line Options

```bash
--url TEXT              Base URL (default: http://localhost:8000)
--users INTEGER         Concurrent users (default: 100)
--requests INTEGER      Requests per user (default: 10)
--export TEXT          Export results to JSON file
```

### Output Example

```
================================================================================
LOAD TEST CONFIGURATION
================================================================================
Base URL: http://localhost:8000
Concurrent Users: 100
Requests per User: 10
Total Requests: 1000
================================================================================

Launching concurrent users...

================================================================================
LOAD TEST RESULTS
================================================================================
Total Time: 28.45s
Requests/Second: 35.15
================================================================================

LATENCY METRICS (ms)
================================================================================
Min:            2.45 ms
Max:          145.32 ms
Avg:           18.92 ms
Median:        16.54 ms
StDev:          8.23 ms
P50:           16.54 ms
P95:           35.67 ms
P99:           62.14 ms
================================================================================

REQUEST METRICS
================================================================================
Total Requests:         1000
Successful:              998
Failed:                    2
Error Rate:              0.20%
================================================================================
```

### JSON Export Format

```json
{
  "timestamp": "2026-01-28T10:30:45.123456",
  "configuration": {
    "base_url": "http://localhost:8000",
    "num_users": 100,
    "requests_per_user": 10
  },
  "metrics": {
    "min_ms": 2.45,
    "max_ms": 145.32,
    "avg_ms": 18.92,
    "p50_ms": 16.54,
    "p95_ms": 35.67,
    "p99_ms": 62.14,
    "median_ms": 16.54,
    "stdev_ms": 8.23,
    "total_requests": 1000,
    "successful_requests": 998,
    "failed_requests": 2,
    "error_rate": 0.2
  },
  "duration_seconds": 28.45
}
```

### Usage Examples

#### Example 1: Quick Sanity Check

```bash
# Light test: 10 users, 5 requests each
python scripts/load_test_asyncio.py --users 10 --requests 5
```

**Use when:** Testing API is working before heavy load

---

#### Example 2: Standard Production Test

```bash
# Standard test: 100 users, 10 requests each
python scripts/load_test_asyncio.py \
  --users 100 \
  --requests 10 \
  --export results/baseline.json
```

**Use when:** Measuring current performance baseline

---

#### Example 3: Peak Load Test

```bash
# Heavy test: 500 users, 20 requests each
python scripts/load_test_asyncio.py \
  --users 500 \
  --requests 20 \
  --export results/peak_load.json
```

**Use when:** Testing maximum capacity

---

#### Example 4: Stress Test

```bash
# Extreme test: 1000 users, 5 requests each
python scripts/load_test_asyncio.py \
  --users 1000 \
  --requests 5 \
  --export results/stress_test.json
```

**Use when:** Finding breaking points

---

#### Example 5: Remote Server

```bash
# Test remote API
python scripts/load_test_asyncio.py \
  --url https://api.example.com \
  --users 50 \
  --requests 10
```

---

### Interpreting Results

#### Latency Metrics

```
Metric     | Range        | Interpretation
-----------|--------------|----------------------------------------
Min        | Any          | Fastest response (ideal case)
Max        | Any          | Slowest response (worst case)
Avg        | < 100ms      | ✓ Good
           | 100-500ms    | ⚠ Acceptable
           | > 500ms      | ✗ Poor
P95        | < 50ms       | ✓ Excellent
           | 50-200ms     | ✓ Good
           | > 200ms      | ⚠ Consider optimization
P99        | < 100ms      | ✓ Excellent
           | 100-500ms    | ✓ Good
           | > 500ms      | ⚠ Outliers present
```

#### Request Metrics

```
Metric        | Target     | Interpretation
--------------|------------|----------------------------------------
Success Rate  | > 99.9%    | ✓ Healthy
              | 99-99.9%   | ⚠ Minor issues
              | < 99%      | ✗ Serious issues
Error Rate    | < 0.1%     | ✓ Excellent
              | 0.1-1%     | ⚠ Monitor closely
              | > 1%       | ✗ Fix required
```

#### Performance Goals

```
Use Case                 | Avg Latency | P95 Latency | P99 Latency
------------------------|-----------  |-------------|-------------
E-commerce Search        | < 100ms     | < 200ms     | < 500ms
Real-time Recommendation | < 50ms      | < 100ms     | < 200ms
Background Processing    | < 500ms     | < 1000ms    | < 2000ms
```

---

## Locust Load Test

### Features

- ✅ Real-time web dashboard
- ✅ Live performance charts
- ✅ User spawn rate control
- ✅ Multiple task types
- ✅ Advanced reporting
- ✅ HTML + JSON export

### Installation

```bash
pip install locust
```

### Starting Locust

```bash
# Basic start
locust -f scripts/load_test_locust.py --host=http://localhost:8000

# With initial settings
locust -f scripts/load_test_locust.py \
  --host=http://localhost:8000 \
  --users=100 \
  --spawn-rate=10

# Headless mode (CLI only, no UI)
locust -f scripts/load_test_locust.py \
  --host=http://localhost:8000 \
  --users=100 \
  --spawn-rate=10 \
  --run-time 5m \
  --headless
```

### Web Interface

1. Open http://localhost:8089
2. Enter:
   - **Number of users:** 100
   - **Spawn rate:** 10 users/second
3. Click "Start Swarming"

### Locust Output

The web dashboard shows:
- **Current user count** (live updating)
- **Requests/second**
- **Response time graph**
- **Failure rate**
- **Statistics table** (min, max, avg, median, p50, p95, p99)
- **Charts** (response times, users over time)

### Export Results

In Locust web UI:
1. Click "Download Data"
2. Select format (CSV or HTML)
3. Save report

---

## Comparing AsyncIO vs Locust

### Use AsyncIO When:

✅ Running in CI/CD pipeline
✅ Need programmatic control
✅ No UI required
✅ Fast, lightweight testing
✅ Minimal dependencies
✅ Exporting to JSON for analysis

### Use Locust When:

✅ Manual exploration needed
✅ Real-time monitoring required
✅ Team collaboration (share URL)
✅ Visual graphs helpful
✅ Testing interactively
✅ Generating HTML reports

---

## Performance Benchmarking Scenarios

### Scenario 1: Baseline Performance

```bash
# Establish baseline
python scripts/load_test_asyncio.py \
  --users 50 \
  --requests 20 \
  --export baseline.json

# Expected: Understand normal performance
# Typical: 15-25ms average latency
```

### Scenario 2: Sustained Load

```bash
# Can system handle consistent traffic?
python scripts/load_test_asyncio.py \
  --users 100 \
  --requests 50 \
  --export sustained_load.json

# Expected: Performance stable over time
# Typical: < 5% variance in latency
```

### Scenario 3: Peak Traffic

```bash
# Handle 5x normal load?
python scripts/load_test_asyncio.py \
  --users 500 \
  --requests 20 \
  --export peak_traffic.json

# Expected: Service remains responsive
# Typical: P95 < 100ms at peak
```

### Scenario 4: Stress Test

```bash
# Find breaking point
python scripts/load_test_asyncio.py \
  --users 1000 \
  --requests 10 \
  --export stress_test.json

# Expected: Identify failure threshold
# Result: Determines max capacity
```

---

## Analyzing Results

### Comparing Multiple Tests

```python
import json
import statistics

# Load multiple test results
tests = {}
for filename in ["baseline.json", "peak_load.json", "stress_test.json"]:
    with open(filename) as f:
        tests[filename] = json.load(f)

# Compare average latency
print("Average Latency Comparison:")
for name, data in tests.items():
    avg = data["metrics"]["avg_ms"]
    print(f"  {name}: {avg:.2f}ms")

# Calculate regression
baseline_avg = tests["baseline.json"]["metrics"]["avg_ms"]
peak_avg = tests["peak_load.json"]["metrics"]["avg_ms"]
regression = ((peak_avg - baseline_avg) / baseline_avg) * 100
print(f"\nLatency regression at peak load: {regression:+.1f}%")
```

### Performance Degradation Tracking

```bash
# Run test and save with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
python scripts/load_test_asyncio.py \
  --users 100 \
  --requests 10 \
  --export results/test_${TIMESTAMP}.json

# Track trends over time
python analyze_load_tests.py results/test_*.json
```

---

## Troubleshooting

### Error: "Connection refused"

```
Problem: API not running
Solution:
  1. Verify API started: http://localhost:8000/docs
  2. Check port: ps aux | grep 8000
  3. Start API if needed: uvicorn main:app --reload
```

### Error: "Too many open files"

```
Problem: System resource limit
Solution:
  # Increase file descriptor limit (Linux/Mac)
  ulimit -n 4096
  
  # Then retry with fewer users
  python scripts/load_test_asyncio.py --users 200
```

### Error: "Address already in use"

```
Problem: Locust port (8089) already in use
Solution:
  # Use different port
  locust -f scripts/load_test_locust.py \
    --host=http://localhost:8000 \
    --web-port=8090
```

### Very High P95/P99 Latency

```
Possible causes:
  1. API under heavy load
  2. Database slow queries
  3. Network latency
  4. System resource constraints

Debug:
  1. Check server CPU/memory usage
  2. Monitor database query times
  3. Profile API with smaller loads
  4. Check network connectivity
```

### All Requests Failing

```
Check:
  1. API is running: curl http://localhost:8000/docs
  2. Endpoint exists: POST /search/text
  3. Payload format correct (see API docs)
  4. No authentication required
  5. CORS enabled if cross-origin
```

---

## Performance Tuning

### After identifying bottlenecks:

1. **High P95/P99 latency:**
   - Add caching for popular queries
   - Optimize vector search parameters
   - Profile slow queries

2. **High error rate:**
   - Increase timeout values
   - Add retry logic
   - Check API logs

3. **Memory issues:**
   - Reduce concurrent users
   - Use connection pooling
   - Monitor memory leaks

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Load Test

on: [push]

jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Start API
        run: |
          pip install -r requirements.txt
          uvicorn main:app &
          sleep 5
      
      - name: Run load test
        run: |
          python scripts/load_test_asyncio.py \
            --users 100 \
            --requests 10 \
            --export results.json
      
      - name: Check results
        run: |
          python scripts/check_performance.py results.json
      
      - name: Upload results
        uses: actions/upload-artifact@v2
        with:
          name: load-test-results
          path: results.json
```

---

## Summary

| Need | Tool | Command |
|------|------|---------|
| Quick test | AsyncIO | `python load_test_asyncio.py` |
| Standard test | AsyncIO | `python load_test_asyncio.py --users 100 --export results.json` |
| Interactive UI | Locust | `locust -f load_test_locust.py --host=http://localhost:8000` |
| Stress test | AsyncIO | `python load_test_asyncio.py --users 1000 --requests 5` |
| CI/CD | AsyncIO | See example above |
| Team testing | Locust | Open web UI on shared server |

Start with AsyncIO for programmatic testing, switch to Locust for interactive exploration.
