# Experiment Analysis Script - Quick Reference

## What It Does

```
Experiment Logs (JSON/MongoDB)
           ↓
      Load Data
           ↓
   Calculate CTR & Metrics
           ↓
   Generate Visualizations
           ↓
    Results (JSON + PNG)
```

## Quick Start (60 seconds)

### 1. Run with Sample Data
```bash
cd c:\omnisearch
python scripts/analyze_experiment_results.py \
  --json logs/sample_experiments.json \
  --output-dir analysis_output
```

### 2. View Results
```bash
# Windows - open PNG files
start analysis_output/dashboard.png
start analysis_output/ctr_comparison.png

# View results JSON
type analysis_output/results.json
```

### 3. Export Results
```bash
python scripts/analyze_experiment_results.py \
  --json logs/sample_experiments.json \
  --output-dir analysis_output \
  --export analysis_output/results.json
```

## Output Files

| File | Description |
|------|-------------|
| `ctr_comparison.png` | V1 vs V2 CTR bar chart |
| `clicks_impressions.png` | Clicks vs impressions grouped bars |
| `response_times.png` | Response time comparison |
| `user_engagement.png` | User counts & engagement metrics |
| `dashboard.png` | 6-panel comprehensive dashboard |
| `results.json` | Machine-readable metrics export |

## Key Metrics

### CTR (Click-Through Rate)
```
CTR = (Clicks / Impressions) × 100%

Example:
V1: 4 clicks / 10 impressions = 40%
V2: 6 clicks / 10 impressions = 60%

V2 is 50% better (+50% improvement)
```

### Response Time
```
Lower is better for user experience

V1: 43.9ms (faster)
V2: 50.5ms (slower but better CTR)
```

### User Engagement
```
Avg Clicks per User shows activity level

V1: 0.40 clicks/user
V2: 0.60 clicks/user

V2 users are 50% more engaged
```

## Command Line Options

```bash
# From JSON file
--json logs/experiments.json

# From MongoDB
--mongodb mongodb://localhost:27017

# MongoDB database name (default: omnisearch)
--db-name omnisearch

# Output directory (default: output)
--output-dir analysis_output

# Export results JSON
--export results.json

# Skip generating plots
--no-plots
```

## Usage Examples

### Basic Analysis
```bash
python scripts/analyze_experiment_results.py --json logs/data.json
```

### With Custom Output Directory
```bash
python scripts/analyze_experiment_results.py \
  --json logs/data.json \
  --output-dir my_results
```

### MongoDB with Export
```bash
python scripts/analyze_experiment_results.py \
  --mongodb mongodb://localhost:27017 \
  --db-name omnisearch \
  --export summary.json
```

### Analysis Only (No Plots)
```bash
python scripts/analyze_experiment_results.py \
  --json logs/data.json \
  --no-plots
```

## Expected Output

### Console Output
```
Loading from JSON: logs/sample_experiments.json
Loaded 30 events

============================================================
EXPERIMENT RESULTS SUMMARY
============================================================

Variant: search_v1
├─ CTR: 40.00%
├─ Clicks: 4
├─ Impressions: 10
├─ Users: 10
├─ Avg clicks/user: 0.40
└─ Avg response time: 43.9ms

Variant: search_v2
├─ CTR: 60.00%
├─ Clicks: 6
├─ Impressions: 10
├─ Users: 10
├─ Avg clicks/user: 0.60
└─ Avg response time: 50.5ms

============================================================
COMPARISON
============================================================
Variant: search_v1 vs search_v2
CTR Improvement: +50.0%
Winner: search_v2 (by 50.0%)
============================================================
```

### Visualization Examples

**ctr_comparison.png:**
```
  60% │           ██
     │           ██
  40% │  ██       ██
     │  ██       ██
   0% └──────────────
       V1      V2
```

**dashboard.png:**
```
┌─────────────────────┬──────────────────────┐
│ CTR: 40% vs 60%     │ Impressions: 10 each │
├─────────────────────┼──────────────────────┤
│ Response: 43 vs 50  │ Users: 10 each       │
├─────────────────────┼──────────────────────┤
│ Engagement: 0.4 vs  │ WINNER: V2 by +50%   │
│           0.6       │                      │
└─────────────────────┴──────────────────────┘
```

## JSON Format

### Input Format
```json
{
  "events": [
    {
      "type": "impression",
      "user_id": "user123",
      "variant": "search_v1",
      "timestamp": "2024-01-15T10:00:00",
      "response_time_ms": 45.2
    },
    {
      "type": "click",
      "user_id": "user123",
      "variant": "search_v1",
      "timestamp": "2024-01-15T10:00:02",
      "response_time_ms": 45.2
    }
  ]
}
```

### Output Format (results.json)
```json
{
  "timestamp": "2024-01-15T15:30:45",
  "variants": {
    "search_v1": {
      "ctr": "0.4000",
      "ctr_percent": "40.00%",
      "clicks": 4,
      "impressions": 10,
      "total_users": 10,
      "avg_clicks_per_user": "0.40",
      "avg_response_time_ms": "43.9"
    },
    "search_v2": {
      "ctr": "0.6000",
      "ctr_percent": "60.00%",
      "clicks": 6,
      "impressions": 10,
      "total_users": 10,
      "avg_clicks_per_user": "0.60",
      "avg_response_time_ms": "50.5"
    }
  }
}
```

## Interpreting Results

### V2 is Better When:
- ✅ CTR is higher
- ✅ Similar or lower response times
- ✅ More user engagement

### V2 Trade-offs:
- ⚠️ Higher response time (acceptable if CTR gain > 10%)
- ⚠️ Lower CTR (may need different tuning)

### Statistical Significance
```
Sample size (impressions per variant):
< 100     = Use with caution
100-1000  = More reliable
1000+     = Highly reliable

CTR Difference:
< 2%      = Likely noise
2-5%      = Likely significant
> 5%      = Very significant
```

## Troubleshooting

### "File not found"
```bash
# Check file exists
ls -la logs/experiments.json

# Use full path
python scripts/analyze_experiment_results.py \
  --json C:\omnisearch\logs\experiments.json
```

### "KeyError: 'type'"
```
JSON must have "type" field: "impression" or "click"
Check JSON format in sample_experiments.json
```

### "pymongo not installed"
```bash
pip install pymongo
```

### No plots generated
```bash
# Check output directory
ls -la analysis_output/

# Verify matplotlib installed
pip install matplotlib
```

## Advanced Tips

### Filter Events by Time (in script)
```python
from datetime import datetime, timedelta
cutoff = datetime.now() - timedelta(days=7)  # Last 7 days
if event.get('timestamp') > cutoff:
    # Process
```

### Custom Colors
```python
self.colors = {
    'search_v1': '#FF0000',  # Red
    'search_v2': '#00FF00',  # Green
}
```

### Higher Resolution Plots
```python
plt.savefig(filepath, dpi=600)  # Instead of 300
```

## Full Documentation

See [EXPERIMENT_ANALYSIS_GUIDE.md](../docs/EXPERIMENT_ANALYSIS_GUIDE.md) for:
- Detailed metrics explanations
- Integration examples
- Advanced usage
- CI/CD pipeline setup

## Files

| File | Purpose |
|------|---------|
| `scripts/analyze_experiment_results.py` | Main analysis script |
| `logs/sample_experiments.json` | Sample test data |
| `docs/EXPERIMENT_ANALYSIS_GUIDE.md` | Full documentation |

## Performance

```
Event Count  | Time   | File Size
10           | < 0.5s | 5 KB
100          | < 0.5s | 50 KB
1,000        | < 1s   | 500 KB
10,000       | 1-2s   | 5 MB
100,000+     | 5-30s  | 50+ MB
```

---

**Ready to go?** Run this:
```bash
python scripts/analyze_experiment_results.py --json logs/sample_experiments.json --output-dir analysis_output
```

Check `analysis_output/dashboard.png` for results!
