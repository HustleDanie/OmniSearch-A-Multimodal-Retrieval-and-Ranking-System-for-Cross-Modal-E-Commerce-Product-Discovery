# HNSW vs IVF: Configuration Quick Reference

## Decision Tree

```
┌─ What's your dataset size?
│
├─ < 1M vectors?
│  │
│  ├─ Recall critical? → HNSW (high)
│  │
│  ├─ Speed critical? → HNSW (speed optimized)
│  │
│  └─ Memory limited? → HNSW (memory optimized)
│
├─ 1M - 10M vectors?
│  │
│  ├─ Can afford > 2GB RAM? → HNSW
│  │
│  └─ Need < 10ms latency? → IVF (balanced)
│
└─ > 10M vectors?
   │
   ├─ Recall > 95% required? → IVF (high recall)
   │
   └─ Speed critical? → IVF (large scale)
```

---

## HNSW Configuration Templates

### Template 1: High Recall (Default)
**Use for:** E-commerce, medical search, critical matching
```python
"vectorIndexConfig": {
    "ef": 128,              # Query time parameter
    "efConstruction": 200,  # Build time parameter
    "maxConnections": 32,   # Graph density
    "dynamicEfMin": 100,    # Min ef
    "dynamicEfMax": 500,    # Max ef
}
```
**Result:** ~97% recall, 10-15ms query, 1.8GB/1M vectors

---

### Template 2: Speed Optimized
**Use for:** Real-time applications, latency critical
```python
"vectorIndexConfig": {
    "ef": 64,
    "efConstruction": 100,
    "maxConnections": 16,
    "dynamicEfMin": 50,
    "dynamicEfMax": 200,
}
```
**Result:** ~85% recall, 3-5ms query, 1.4GB/1M vectors

---

### Template 3: Memory Optimized
**Use for:** Constrained resources, on-device
```python
"vectorIndexConfig": {
    "ef": 96,
    "efConstruction": 150,
    "maxConnections": 12,   # Minimum viable
    "dynamicEfMin": 80,
    "dynamicEfMax": 300,
}
```
**Result:** ~92% recall, 6-8ms query, 1.2GB/1M vectors

---

### Template 4: Maximum Recall
**Use for:** Critical applications, archives
```python
"vectorIndexConfig": {
    "ef": 256,
    "efConstruction": 500,
    "maxConnections": 64,   # Maximum viable
    "dynamicEfMin": 200,
    "dynamicEfMax": 1000,
}
```
**Result:** ~99%+ recall, 40-50ms query, 2.8GB/1M vectors

---

## IVF Configuration Templates

### Template 1: Balanced (Default)
**Use for:** General purpose, 100K-1M vectors
```python
"vectorIndexConfig": {
    "nlist": 1024,          # √1M
    "nprobe": 20,           # 2% of clusters
}
```
**Result:** ~90% recall, 8-12ms query

---

### Template 2: High Recall
**Use for:** When recall > 95% matters
```python
"vectorIndexConfig": {
    "nlist": 1024,
    "nprobe": 256,          # 25% of clusters
    "hnswEf": 300,          # HNSW secondary level
}
```
**Result:** ~97% recall, 40-60ms query

---

### Template 3: Large Scale (10M+ vectors)
**Use for:** 10M to 100M+ vectors
```python
"vectorIndexConfig": {
    "nlist": 10000,         # √10M
    "nprobe": 64,           # 0.6% of clusters
    "hnswEf": 200,
}
```
**Result:** ~88% recall, 15-25ms query

---

### Template 4: Ultra-Fast (Speed Priority)
**Use for:** < 5ms latency required
```python
"vectorIndexConfig": {
    "nlist": 2048,          # More clusters
    "nprobe": 8,            # 0.4% of clusters
}
```
**Result:** ~78% recall, 2-5ms query

---

## Parameter Tuning Guide

### For HNSW

| Goal | Change | Effect |
|------|--------|--------|
| Improve Recall | ↑ ef, efConstruction, maxConnections | +Recall, -Speed, +Memory |
| Reduce Query Time | ↓ ef, dynamicEfMax | -Recall, +Speed, -Memory |
| Reduce Build Time | ↓ efConstruction, maxConnections | -Recall, +Speed |
| Reduce Memory | ↓ maxConnections | -Recall, +Speed |

### For IVF

| Goal | Change | Effect |
|------|--------|--------|
| Improve Recall | ↑ nprobe, nlist | +Recall, -Speed |
| Reduce Query Time | ↓ nprobe | -Recall, +Speed |
| Better for Large Data | ↑ nlist, ↑ nprobe % | Balanced scaling |

---

## Specific Use Cases

### E-Commerce (1M Products)

```python
{
    "class": "Product",
    "vectorIndexType": "hnsw",
    "vectorIndexConfig": {
        "ef": 128,
        "efConstruction": 200,
        "maxConnections": 32,
    }
}
# Justification:
# - 1M is sweet spot for HNSW
# - Recall critical for UX
# - Query time < 50ms acceptable
# - 1.8GB memory acceptable
```

---

### Real-Time Recommendations (10M Users)

```python
{
    "class": "UserProfile",
    "vectorIndexType": "ivf",
    "vectorIndexConfig": {
        "nlist": 3162,
        "nprobe": 32,       # 1% search
        "hnswEf": 150,
    }
}
# Justification:
# - 10M scale favors IVF
# - Speed critical (< 10ms)
# - IVF: 8ms vs HNSW: 20ms
# - Memory 30% better
```

---

### Legal Document Archive (100M)

```python
{
    "class": "LegalDocument",
    "vectorIndexType": "ivf",
    "vectorIndexConfig": {
        "nlist": 10000,
        "nprobe": 512,      # 5% search for recall
        "hnswEf": 300,
    }
}
# Justification:
# - 100M too large for HNSW
# - Recall critical
# - Batch queries OK (50-100ms)
# - IVF only viable option
```

---

### Mobile On-Device (10K Vectors)

```python
{
    "class": "LocalDocument",
    "vectorIndexType": "hnsw",
    "vectorIndexConfig": {
        "ef": 80,
        "efConstruction": 100,
        "maxConnections": 8,    # Minimal
        "flatSearchCutoff": 10000,
    }
}
# Justification:
# - Small dataset: linear search fallback
# - Memory critical (< 50MB)
# - maxConnections=8 saves 60% memory
# - Decent recall still achievable
```

---

## Performance Benchmarks

### Query Latency (Single Vector)

```
Dataset: 1M vectors (384-dim)

HNSW:
  ef=64:  3ms   (85% recall)
  ef=128: 10ms  (97% recall)
  ef=256: 50ms  (99% recall)

IVF:
  nprobe=8:   5ms   (80% recall)
  nprobe=20:  12ms  (90% recall)
  nprobe=256: 60ms  (97% recall)
```

### Build Time

```
Dataset: 1M vectors (384-dim)

HNSW:
  maxConnections=12: 20 min
  maxConnections=32: 45 min
  maxConnections=64: 90 min

IVF:
  nlist=512:  5 min
  nlist=1024: 10 min
  nlist=2048: 20 min

IVF is 4-10x faster to build
```

### Memory Usage

```
1M vectors, 384-dim (4 bytes per float)

Base Embeddings: 1.5 GB (both)

HNSW Overhead:
  maxConnections=12: +0.2 GB = 1.7 GB
  maxConnections=32: +0.5 GB = 2.0 GB
  maxConnections=64: +1.0 GB = 2.5 GB

IVF Overhead:
  nlist=512:  +0.01 GB = 1.51 GB
  nlist=1024: +0.01 GB = 1.51 GB
  nlist=4096: +0.01 GB = 1.51 GB

IVF uses 25-40% less memory
```

---

## Migration Checklist

### HNSW → IVF (Scaling Out)

- [ ] Calculate recommended nlist = √(new_size)
- [ ] Set nprobe = nlist / 50 (for 90% recall baseline)
- [ ] Create new IVF collection
- [ ] Batch migrate vectors from HNSW collection
- [ ] Verify recall on sample queries
- [ ] Increase nprobe if recall drops below target
- [ ] Update client configuration
- [ ] Monitor query performance for 24 hours
- [ ] Archive old HNSW collection

### Tuning After Migration

```
If recall < target:
  1. Try: nprobe *= 2
  2. If still low: hnswEf *= 1.5
  3. Last resort: rebuild with nlist *= 2

If queries too slow:
  1. Try: nprobe /= 2
  2. If needed: nlist *= 1.5 (requires rebuild)
```

---

## Common Mistakes & Fixes

### ❌ HNSW too slow with large dataset

```python
# Wrong (HNSW with 50M vectors)
"vectorIndexType": "hnsw",
"vectorIndexConfig": {"maxConnections": 32}
# Result: 5-10 minute query lag!

# ✓ Right (use IVF instead)
"vectorIndexType": "ivf",
"vectorIndexConfig": {"nlist": 7071, "nprobe": 50}
```

### ❌ IVF recall too low

```python
# Wrong
"vectorIndexConfig": {
    "nlist": 1024,
    "nprobe": 1,  # Only checking 0.1% of clusters!
}

# ✓ Right
"vectorIndexConfig": {
    "nlist": 1024,
    "nprobe": 50,  # Check ~5% of clusters
}
```

### ❌ HNSW memory explosion

```python
# Wrong (on server with 4GB RAM)
"vectorIndexConfig": {
    "maxConnections": 64,  # 64 × 8 bytes × 1M = 512MB overhead!
}

# ✓ Right
"vectorIndexConfig": {
    "maxConnections": 16,  # 16 × 8 bytes × 1M = 128MB
}
```

---

## Monitoring Queries

```python
# Check current performance
import weaviate
from datetime import datetime, timedelta

client = weaviate.connect_to_local()

# Get index config
collection = client.collections.get("Document")
config = collection.config
print(f"Index Type: {config.vector_index_type}")
print(f"Index Config: {config.vector_index_config}")

# Measure query latency
import time
queries = []
for i in range(100):
    start = time.time()
    result = collection.query.near_vector(
        near_vector=[...],  # Your vector
        limit=10
    ).objects
    queries.append(time.time() - start)

print(f"Avg: {sum(queries)/len(queries)*1000:.2f}ms")
print(f"P99: {sorted(queries)[99]*1000:.2f}ms")
```

---

## When to Rebuild Index

### HNSW Rebuild Needed If:
- ❌ Query latency increased > 50%
- ❌ Detected memory leak (objects accumulating)
- ❌ Changing maxConnections (requires rebuild)
- ❌ Index corruption suspected

### IVF Rebuild Needed If:
- ❌ Recall dropped significantly (query distribution changed)
- ❌ Cluster imbalance detected (some clusters 10x larger)
- ❌ Changing nlist (requires rebuild)
- ❌ Performance degraded after many deletes

---

## Decision Matrix

```
┌──────────────────┬─────────────────┬──────────────────┐
│ Requirement      │ Choose HNSW     │ Choose IVF       │
├──────────────────┼─────────────────┼──────────────────┤
│ < 1M vectors     │ ✓ Yes           │ ✓ OK             │
│ 1M - 10M vectors │ ✓ Yes (if RAM)  │ ✓ Yes            │
│ > 10M vectors    │ ✗ No            │ ✓ Yes            │
│ Recall > 98%     │ ✓ Yes           │ Possible (slow)  │
│ Query < 5ms      │ ✓ Possible      │ ✓ Yes            │
│ Query < 50ms     │ ✓ Yes           │ ✓ Yes            │
│ Build < 1min     │ ✗ No            │ ✓ Yes            │
│ Memory < 2GB     │ ✓ Yes           │ ✓ Yes            │
└──────────────────┴─────────────────┴──────────────────┘
```

---

## Summary

| Aspect | HNSW | IVF |
|--------|------|-----|
| **Use When** | Small datasets, recall critical | Large datasets, speed matters |
| **Max Vectors** | ~100M (practical) | 1B+ |
| **Tuning Complexity** | Medium (6 params) | Low (2 params) |
| **Build Speed** | Slow | Very fast |
| **Query Speed** | Fast | Very fast |
| **Memory** | Higher | Lower |
| **Parameters** | ef, efConstruction, maxConnections | nlist, nprobe |
| **Sweet Spot** | 1K - 10M | 100K - 1B |

**Default Choice:** HNSW for most cases. Switch to IVF when dataset > 10M or query speed critical.
