# HNSW vs IVF Index Settings in Weaviate

## Quick Comparison

| Aspect | HNSW | IVF |
|--------|------|-----|
| **Algorithm** | Hierarchical Navigable Small World | Inverted File with Flat (or HNSW) indexing |
| **Search Speed** | ⚡ Very Fast | ⚡⚡ Moderate (large datasets) |
| **Recall** | 🎯 Excellent (>95%) | 🎯 Good (configurable 85-99%) |
| **Memory** | 💾 Medium-High | 💾 Lower (with quantization) |
| **Build Time** | ⏱️ Medium | ⏱️ Slow |
| **Best For** | Smaller datasets, recall priority | Large datasets, speed priority |
| **Scalability** | ✓ Good (< 10M vectors) | ✓✓ Excellent (10M+ vectors) |

---

## HNSW (Hierarchical Navigable Small World)

### What It Does

HNSW builds a hierarchical graph structure where vectors are connected as a network. Search navigates through layers from coarse to fine-grained matches.

```
Layer 2 (Coarse):    •——•  Fast navigation
                     |  |  between clusters
Layer 1 (Medium):   •—•—•—•  Refine candidates
                    | | | |
Layer 0 (Fine):    •••••••  Exact search
```

### Configuration in Weaviate

```python
from weaviate.classes.config import Configure, Property, DataType, IndexType

# Method 1: Using Configure helper
schema = {
    "classes": [
        {
            "class": "Document",
            "properties": [
                Property(
                    name="content",
                    data_type=DataType.TEXT,
                )
            ],
            # HNSW Configuration
            "vectorIndexType": IndexType.HNSW,
            "vectorIndexConfig": {
                "ef": 128,                    # Search time tradeoff
                "efConstruction": 200,        # Build time parameter
                "maxConnections": 32,         # Connections per node
                "dynamicEfMin": 100,          # Min ef during search
                "dynamicEfMax": 500,          # Max ef during search
                "dynamicEfFactor": 8,         # Multiplication factor
                "flatSearchCutoff": 40000,    # Switch to linear after threshold
                "skip": False,                # Enable/disable index
                "cleanupIntervalSeconds": 300, # Maintenance interval
            }
        }
    ]
}
```

### HNSW Parameters Explained

| Parameter | Range | Default | Impact |
|-----------|-------|---------|--------|
| **ef** | 1-1000 | 128 | Higher = better recall, slower search. Search time parameter. |
| **efConstruction** | 1-1000 | 200 | Higher = better recall during indexing, slower build. Only at creation. |
| **maxConnections** | 4-64 | 32 | Higher = better recall, more memory. Cannot change after creation. |
| **dynamicEfMin** | 1-500 | 100 | Minimum ef during search (performance guarantee). |
| **dynamicEfMax** | 500-5000 | 500 | Maximum ef during search (recall limit). |
| **dynamicEfFactor** | 1-10 | 8 | Multiplier for ef based on result count. |
| **flatSearchCutoff** | 1000-1000000 | 40000 | Falls back to linear search if dataset smaller than this. |

### Configuration Examples

#### Scenario 1: High Recall (Default)
```python
vectorIndexConfig = {
    "ef": 128,
    "efConstruction": 200,
    "maxConnections": 32,
    "dynamicEfMin": 100,
    "dynamicEfMax": 500,
}
# Result: ~98% recall, ~10ms query time
```

#### Scenario 2: Speed Optimized
```python
vectorIndexConfig = {
    "ef": 64,                # Reduce search parameter
    "efConstruction": 100,   # Reduce build parameter
    "maxConnections": 16,    # Fewer connections
    "dynamicEfMin": 50,      # Lower min ef
    "dynamicEfMax": 200,     # Lower max ef
}
# Result: ~85% recall, ~3ms query time
```

#### Scenario 3: Memory Optimized
```python
vectorIndexConfig = {
    "ef": 96,
    "efConstruction": 150,
    "maxConnections": 12,    # Minimum connections
    "dynamicEfMin": 80,
    "dynamicEfMax": 300,
}
# Result: ~92% recall, ~6ms query time, -40% memory
```

#### Scenario 4: Maximum Recall
```python
vectorIndexConfig = {
    "ef": 256,               # Maximum search
    "efConstruction": 500,   # Maximum build
    "maxConnections": 64,    # Maximum connections
    "dynamicEfMin": 200,
    "dynamicEfMax": 1000,
}
# Result: ~99%+ recall, ~50ms query time
```

### HNSW Memory Usage

```
Memory per vector = base_overhead + (ef * graph_size)

Example for 1M vectors (384-dim):
- Base: ~5 bytes × 1M = 5 MB
- Graph overhead: ~maxConnections × pointer_size × 1M
  = 32 × 8 bytes × 1M = 256 MB
- Total graph: ~260 MB
- Vector embeddings: 384 × 4 bytes × 1M = 1.5 GB
- Total HNSW index: ~1.76 GB
```

---

## IVF (Inverted File Index)

### What It Does

IVF partitions the vector space into clusters (codebook), then performs exhaustive search within relevant clusters rather than the entire space.

```
Codebook (K clusters):
Cluster 1 •——— vectors 1, 5, 9, 15
Cluster 2 •——— vectors 2, 7, 11, 18
Cluster 3 •——— vectors 3, 4, 6, 12

Query: Find in nearest K clusters only
(Not all M clusters)
```

### Configuration in Weaviate

```python
from weaviate.classes.config import Configure, Property, DataType, IndexType

# IVF Configuration
schema = {
    "classes": [
        {
            "class": "Document",
            "properties": [
                Property(
                    name="content",
                    data_type=DataType.TEXT,
                )
            ],
            # IVF Configuration
            "vectorIndexType": IndexType.IVF,
            "vectorIndexConfig": {
                "nlist": 1024,                # Number of cluster centers
                "nprobe": 20,                 # Number of clusters to search
                "hnswEf": 200,                # If HNSW in second-level index
                "skip": False,
            }
        }
    ]
}
```

### IVF Parameters Explained

| Parameter | Typical Range | Default | Impact |
|-----------|---------------|---------|--------|
| **nlist** | 32-65536 | 1024 | More clusters = finer partition, slower build. Recommended: √N (N=dataset size) |
| **nprobe** | 1-nlist | 20 | More probes = better recall, slower search. Typically 1-10% of nlist. |
| **hnswEf** | 32-500 | 200 | If using HNSW within clusters, search parameter. |

### IVF Parameter Selection

#### How to Choose nlist (number of clusters)

```
Recommended: nlist ≈ √(dataset_size)

Examples:
- 1K vectors:      nlist = 32
- 10K vectors:     nlist = 100
- 100K vectors:    nlist = 316
- 1M vectors:      nlist = 1,000
- 10M vectors:     nlist = 3,162
- 100M vectors:    nlist = 10,000
```

#### How to Choose nprobe (search clusters)

```
Typical: nprobe = max(1, min(nlist, nlist / 50))

Examples (for nlist=1024):
- Max recall:    nprobe = 256 (25% of clusters)
- Balanced:      nprobe = 64  (6% of clusters)
- Speed optimized: nprobe = 16 (1.5% of clusters)
```

### Configuration Examples

#### Scenario 1: Balanced (Default)
```python
vectorIndexConfig = {
    "nlist": 1024,          # √1M ≈ 1000
    "nprobe": 20,           # 2% of clusters
}
# Result: ~90% recall, ~15ms query time, 100K vectors
```

#### Scenario 2: High Recall
```python
vectorIndexConfig = {
    "nlist": 1024,
    "nprobe": 256,          # 25% of clusters (search more)
    "hnswEf": 300,
}
# Result: ~97% recall, ~50ms query time
```

#### Scenario 3: Speed Optimized
```python
vectorIndexConfig = {
    "nlist": 2048,          # More clusters
    "nprobe": 8,            # Search fewer clusters
}
# Result: ~80% recall, ~5ms query time
```

#### Scenario 4: Large Dataset (10M+ vectors)
```python
vectorIndexConfig = {
    "nlist": 10000,         # √10M ≈ 3162, use 10K
    "nprobe": 64,           # 0.6% of clusters
    "hnswEf": 200,
}
# Result: ~88% recall on 10M vectors, ~20ms query time
```

### IVF Memory Usage

```
Memory per vector = base_overhead + cluster_assignment

Example for 1M vectors (384-dim):
- Vector embeddings: 384 × 4 bytes × 1M = 1.5 GB
- Cluster assignments: 4 bytes × 1M = 4 MB
- Codebook: 384 × 4 bytes × 1024 = 1.5 MB
- Total IVF index: ~1.5 GB
- Overhead: ~1% vs HNSW
```

---

## Tradeoff Analysis

### 1. Recall vs Query Speed

```
HNSW Trade-off Curve:

100% ┤                    ▲ ef=256
     │                   ╱│
 95% ├──────────────────╱ │ ef=128
     │               ╱    │
 90% ├──────────────╱     │ ef=64
     │          ╱         │
 85% ├─────────╱          │
     │    ╱                │
 80% ├──╱                  │
     └─────────────────────┴─────
      1ms  10ms  100ms  1s
      Query Speed →

IVF Trade-off Curve:

100% ┤                    ▲ nprobe=nlist
     │                   ╱│
 95% ├──────────────────╱ │ nprobe=nlist/4
     │               ╱    │
 90% ├──────────────╱     │ nprobe=nlist/64
     │          ╱         │
 80% ├─────────╱          │
     │    ╱                │
 70% ├──╱                  │
     └─────────────────────┴─────
      1ms  10ms  100ms  1s
      Query Speed →
```

### 2. Recall vs Memory

```
HNSW (1M vectors, 384-dim):
maxConnections Memory  Recall  BuildTime
    8          1.2 GB   92%     15min
    16         1.4 GB   94%     25min
    32         1.8 GB   97%     45min
    64         2.8 GB   99%     90min

IVF (1M vectors, 384-dim):
nlist  nprobe   Memory  Recall  BuildTime
 512     8       1.50 GB  85%     5min
1024    20       1.50 GB  90%    10min
2048    64       1.51 GB  95%    20min
4096   256       1.52 GB  98%    40min
```

### 3. Query Speed vs Dataset Size

```
Query Time (ms) vs Dataset Size

        1K    10K   100K   1M    10M   100M
HNSW    0.5   1.2    5.0   10.0  20.0  50.0
IVF     0.3   0.5    2.0    8.0  15.0  25.0

(ef=128 for HNSW, nprobe=20 for IVF)
```

### 4. Build Time Comparison

```
Build Time (minutes) vs Dataset Size

         1K    10K    100K   1M     10M    100M
HNSW     0.1   0.5    5      45     500    5000
IVF      0.01  0.05   0.5    10     100    1000

IVF is 5-50x faster to build
```

---

## Decision Matrix

### Choose HNSW When:

✅ **Recall is Critical**
- E-commerce product search (wrong items hurt UX)
- Medical diagnosis matching
- Legal document retrieval

✅ **Dataset is Small-Medium**
- < 10 million vectors
- Memory available for overhead

✅ **Query Speed is Critical**
- Real-time applications (< 10ms latency)
- Mobile devices with limited resources

✅ **Consistency Required**
- HNSW provides consistent recall
- Query speed is predictable

### Choose IVF When:

✅ **Dataset is Very Large**
- 10+ million vectors
- 100+ million vectors scales well

✅ **Memory is Constrained**
- IVF has lower memory overhead
- Can use quantization with IVF

✅ **Build Speed Matters**
- Need to index frequently
- Adding millions of vectors daily

✅ **Storage Cost Matters**
- IVF is more memory-efficient
- Works better with disk-based storage

---

## Hybrid Strategy: IVF + Quantization

For very large datasets with memory constraints:

```python
# IVF with Product Quantization
vectorIndexConfig = {
    "vectorCacheMaxObjects": 1000000,
    "nlist": 4096,
    "nprobe": 64,
    "skip": False,
}

# Quantization settings (in class schema)
"vectorizeProperties": [],
"vectorizer": "text2vec-transformers",
"moduleConfig": {
    "text2vec-transformers": {
        "vectorizeClassName": False,
        "squeezeWAVIn": True,  # Optimize memory
    }
}
```

**Result:** 4-8x memory reduction with ~10% recall loss

---

## Performance Tuning Examples

### Example 1: E-Commerce Product Search

**Requirements:**
- 1M products (recall critical)
- < 50ms latency acceptable
- 10GB memory available

**Configuration:**
```python
vectorIndexConfig = {
    "ef": 128,
    "efConstruction": 200,
    "maxConnections": 32,
    "dynamicEfMin": 100,
    "dynamicEfMax": 500,
}
# HNSW recommended
# Expected: 97% recall, 15ms query, 1.8GB memory
```

### Example 2: Real-Time Recommendation Engine

**Requirements:**
- 10M user profiles
- < 10ms latency
- Deployment on limited resources

**Configuration:**
```python
vectorIndexConfig = {
    "nlist": 3162,
    "nprobe": 32,
    "hnswEf": 150,
}
# IVF recommended
# Expected: 85% recall, 8ms query, 1.5GB memory
```

### Example 3: Legal Document Archive

**Requirements:**
- 100M documents
- Recall > 95% critical
- Batch queries acceptable (50-100ms OK)

**Configuration:**
```python
# Hybrid approach: IVF for speed, high nprobe for recall
vectorIndexConfig = {
    "nlist": 10000,
    "nprobe": 512,          # High nprobe for recall
    "hnswEf": 300,
}
# Expected: 96% recall, 80ms query, 1.5GB memory
```

---

## Monitoring & Optimization

### Monitor These Metrics

```python
import weaviate
from weaviate.classes.query import MetadataQuery

# Check index statistics
client = weaviate.connect_to_local()

# Get collection info
collection_info = client.collections.get("Document")
print(f"Vector index type: {collection_info.config.vector_index_type}")
print(f"Vector index config: {collection_info.config.vector_index_config}")

# Check collection size
collection_stats = client.collections.get_by_name("Document")
print(f"Object count: {collection_stats.data.aggregate.count}")
```

### Performance Testing

```python
import time
import statistics

# Benchmark query performance
query_times = []
for i in range(100):
    start = time.time()
    results = client.collections.get("Document").query.near_vector(
        near_vector=test_vector,
        limit=10,
        where=None,
    ).objects
    query_times.append(time.time() - start)

print(f"Avg: {statistics.mean(query_times)*1000:.2f}ms")
print(f"P99: {sorted(query_times)[99]*1000:.2f}ms")
print(f"Max: {max(query_times)*1000:.2f}ms")
```

---

## Migration Path

### From HNSW to IVF (for scaling)

```python
# 1. Create new collection with IVF
new_config = {
    "vectorIndexType": IndexType.IVF,
    "vectorIndexConfig": {
        "nlist": 1024,
        "nprobe": 20,
    }
}

# 2. Bulk import from old collection
old_collection = client.collections.get("DocumentHNSW")
new_collection = client.collections.get("DocumentIVF")

batch = new_collection.data.batch()
for obj in old_collection.iterator(
    where=None,
    return_properties=["all"],
):
    batch.add_object(obj.properties, vector=obj.vector)

batch.flush()
print(f"Migrated {batch.current_count} objects")
```

---

## Summary Table

| Feature | HNSW | IVF |
|---------|------|-----|
| **Recall (default)** | 97% | 90% |
| **Query Speed (1M vectors)** | 10ms | 8ms |
| **Build Time (1M vectors)** | 45min | 10min |
| **Memory (1M vectors)** | 1.8GB | 1.5GB |
| **Max Vectors** | 100M | 1B+ |
| **Tuning Parameters** | 6 key params | 2-3 key params |
| **Consistency** | High | Medium |
| **Best Use Case** | Recall-critical | Scale & speed |

---

## References

- [Weaviate HNSW Documentation](https://weaviate.io/developers/weaviate/concepts/vector-index)
- [Weaviate IVF Documentation](https://weaviate.io/developers/weaviate/concepts/vector-index-plugins)
- [HNSW Paper](https://arxiv.org/abs/1802.02413) - Malkov & Yashunin
- [IVF Paper](https://arxiv.org/abs/1702.08734) - Johnson et al.
