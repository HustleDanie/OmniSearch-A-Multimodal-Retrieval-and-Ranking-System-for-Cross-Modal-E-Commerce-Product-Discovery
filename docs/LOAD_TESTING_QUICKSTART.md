# Load Testing Quick Reference

## What You Get

- ✅ **100 concurrent search users simulator**
- ✅ **Latency metrics**: min, max, avg, median, p50, p95, p99, stdev
- ✅ **Request metrics**: total, successful, failed, error rate
- ✅ **Two implementations**: AsyncIO (CLI) and Locust (Web UI)
- ✅ **Result analysis**: Compare tests, generate reports

---

## 30-Second Start

### Option 1: AsyncIO (No UI, Fast)
```bash
# Run test with 100 users
python scripts/load_test_asyncio.py

# Or with options
python scripts/load_test_asyncio.py --users 100 --requests 10 --export results.json
```

### Option 2: Locust (Web UI, Interactive)
```bash
# Install once
pip install locust

# Run and open http://localhost:8089
locust -f scripts/load_test_locust.py --host=http://localhost:8000
```

---

## Output Example

```
LATENCY METRICS (ms)
================================================================================
Min:            2.45 ms
Max:          145.32 ms
Avg:           18.92 ms          ← Key metric
Median:        16.54 ms
P95:           35.67 ms          ← 95% of requests < 35.67ms
P99:           62.14 ms
StDev:          8.23 ms
================================================================================

REQUEST METRICS
================================================================================
Total Requests:         1000
Successful:              998
Failed:                    2
Error Rate:              0.20%   ← Should be < 0.1%
================================================================================
```

---

## Common Commands

```bash
# Light test (quick check)
python scripts/load_test_asyncio.py --users 10 --requests 5

# Standard test (100 users)
python scripts/load_test_asyncio.py --users 100 --requests 10

# Peak load test (500 users)
python scripts/load_test_asyncio.py --users 500 --requests 20

# Stress test (find breaking point)
python scripts/load_test_asyncio.py --users 1000 --requests 5

# Remote server
python scripts/load_test_asyncio.py --url https://api.example.com --users 100

# Save results for comparison
python scripts/load_test_asyncio.py --users 100 --export test1.json

# Analyze results
python scripts/analyze_load_tests.py test1.json test2.json --compare --report
```

---

## Interpreting Results

| Metric | Good | Warning | Bad |
|--------|------|---------|-----|
| **Avg Latency** | < 50ms | 50-100ms | > 100ms |
| **P95 Latency** | < 100ms | 100-200ms | > 200ms |
| **Error Rate** | < 0.1% | 0.1-1% | > 1% |

---

## Files Created

| File | Purpose |
|------|---------|
| `scripts/load_test_asyncio.py` | Main AsyncIO load tester |
| `scripts/load_test_locust.py` | Locust web-based load tester |
| `scripts/analyze_load_tests.py` | Analyze & compare results |
| `docs/LOAD_TESTING_GUIDE.md` | Full documentation |

---

## Workflow

```
1. Run baseline test
   → python scripts/load_test_asyncio.py --users 100 --export baseline.json

2. Make optimization
   → Update search algorithm / add indexes

3. Run test again
   → python scripts/load_test_asyncio.py --users 100 --export optimized.json

4. Compare results
   → python scripts/analyze_load_tests.py baseline.json optimized.json --compare

5. Check improvement
   → Look for lower avg/p95 latency and error rate
```

---

## What to Measure

### During Development
- **Baseline:** Run with default settings to establish baseline
- **After Changes:** Compare metrics to detect regressions
- **Optimization:** Verify fixes improve performance

### Before Production
- **Sustained Load:** 100 users × 50 requests
- **Peak Traffic:** 500 users × 20 requests  
- **Stress Test:** 1000 users × 5 requests

### Ongoing Monitoring
- **Daily:** Light test (50 users) for smoke test
- **Weekly:** Standard test (100 users) for trends
- **Monthly:** Peak load test (500 users) for capacity planning

---

## Performance Goals

### E-Commerce Search
- Avg: < 100ms
- P95: < 200ms
- P99: < 500ms
- Error: < 0.1%

### Real-Time Recommendations
- Avg: < 50ms
- P95: < 100ms
- P99: < 200ms
- Error: < 0.05%

### Background Processing
- Avg: < 500ms
- P95: < 1000ms
- P99: < 2000ms
- Error: < 1%

---

## Debugging Issues

### High Latency
```
1. Check if API is under load
2. Monitor database queries
3. Profile slow endpoints
4. Add caching for popular queries
```

### High Error Rate
```
1. Check API logs
2. Increase timeout values
3. Verify endpoint available
4. Check payload format
```

### Memory Issues
```
1. Use fewer concurrent users
2. Reduce requests per user
3. Monitor system resources
4. Check for memory leaks
```

---

## Exporting Results

```bash
# Export as JSON
python scripts/load_test_asyncio.py --export results.json

# Analyze multiple tests
python scripts/analyze_load_tests.py test1.json test2.json --compare

# Export comparison as CSV
python scripts/analyze_load_tests.py test1.json test2.json \
  --export-csv comparison.csv

# Export HTML report
python scripts/analyze_load_tests.py test1.json test2.json \
  --export-html report.html
```

---

## Tips

✓ **Start small:** Test with 10 users before scaling to 1000
✓ **Warm up:** Make a few test queries before load testing
✓ **Multiple runs:** Run test 2-3 times to check consistency
✓ **Monitor server:** Watch CPU/memory during test
✓ **Test realistic:** Use real search queries similar to production
✓ **Compare fairly:** Same number of users/requests for comparisons
✓ **Document baselines:** Save baseline results for comparison

---

## Full Documentation

See [LOAD_TESTING_GUIDE.md](../docs/LOAD_TESTING_GUIDE.md) for:
- Detailed parameter explanations
- Scenario-based examples
- Result interpretation guide
- CI/CD integration
- Troubleshooting
- Advanced usage

---

## Quick Stats

```
Typical Performance (100 users, 1000 total requests)

                  Min    Avg    P95    Max
Without Index:    45ms   125ms  250ms  800ms  ← Slow
With Index:       5ms    18ms   35ms   145ms  ← Good
With Caching:     2ms    8ms    15ms   50ms   ← Excellent
```

---

## One-Liner Examples

```bash
# Quick sanity check
python scripts/load_test_asyncio.py --users 5 --requests 1

# Standard baseline
python scripts/load_test_asyncio.py --export baseline.json

# Heavy load with export
python scripts/load_test_asyncio.py --users 500 --requests 20 --export heavy.json

# Compare two tests side-by-side
python scripts/analyze_load_tests.py baseline.json heavy.json --compare --report

# Find and test all saved results
python scripts/analyze_load_tests.py --glob "results/*.json" --report --export-csv summary.csv
```

---

**Next steps:** Run your first test to establish a baseline!
