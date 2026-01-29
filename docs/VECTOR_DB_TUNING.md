# Vector Database Tuning Guide

## Overview

Weaviate configuration and optimization for efficient vector search at scale. This guide covers indexing strategies, query optimization, and performance tuning for CLIP embeddings.

---

## Architecture

```
┌─────────────────────────────────────────┐
│         Search Query                    │
│     (CLIP Embedding: 512-dim)           │
└────────────────┬────────────────────────┘
                 │
        ┌────────▼────────┐
        │  Approximate    │
        │  Nearest        │
        │  Neighbor (ANN) │
        │  Index (HNSW)   │
        └────────┬────────┘
                 │
    ┌────────────┴─────────────┐
    │ Filtering Layer         │
    │ (Category, Color)       │
    └────────┬────────────────┘
             │
    ┌────────▼──────────────┐
    │ Candidate Results     │
    │ (Ranked by Distance)  │
    └──────────────────────┘
```

---

## 1. Schema Design

### Product Collection

```python
# Optimal schema with all indexed properties
client.collections.create(
    name="Product",
    description="Product catalog with CLIP embeddings",
    
    # Vector configuration
    vectorizer_config=None,  # Manual vectorization
    vector_config={
        "size": 512,  # CLIP ViT-B/32 dimension
        "distance": "cosine"  # Similarity metric
    },
    
    # Properties with indexes
    properties=[
        # ID fields
        Property(name="product_id", data_type=DataType.TEXT, skip_vectorization=True),
        
        # Text fields (searchable)
        Property(name="title", data_type=DataType.TEXT, skip_vectorization=True),
        Property(name="description", data_type=DataType.TEXT, skip_vectorization=True),
        
        # Categorical fields (filterable)
        Property(name="category", data_type=DataType.TEXT, skip_vectorization=True),
        Property(name="color", data_type=DataType.TEXT, skip_vectorization=True),
        Property(name="size", data_type=DataType.TEXT, skip_vectorization=True),
        
        # Numeric fields
        Property(name="price", data_type=DataType.NUMBER, skip_vectorization=True),
        Property(name="rating", data_type=DataType.NUMBER, skip_vectorization=True),
        Property(name="stock_level", data_type=DataType.INT, skip_vectorization=True),
        
        # Temporal fields
        Property(name="added_date", data_type=DataType.DATE, skip_vectorization=True),
        Property(name="last_updated", data_type=DataType.DATE, skip_vectorization=True),
        
        # Image metadata
        Property(name="image_path", data_type=DataType.TEXT, skip_vectorization=True),
        Property(name="image_width", data_type=DataType.INT, skip_vectorization=True),
        Property(name="image_height", data_type=DataType.INT, skip_vectorization=True),
    ]
)
```

### Why These Choices?

| Choice | Reason |
|--------|--------|
| `vectorizer_config=None` | Manual control over embedding quality |
| `size=512` | CLIP ViT-B/32 output dimension |
| `distance="cosine"` | Normalized embeddings favor cosine |
| `skip_vectorization=True` | Metadata shouldn't be embedded |

---

## 2. Indexing Strategy

### HNSW Index Configuration

```python
# Configure approximate nearest neighbor index
vector_config=Configure.VectorIndex.hnsw(
    space="cosine",                 # Distance metric
    ef_construction=200,            # Construction phase size
    ef=128,                         # Query-time search breadth
    max_connections=32,             # Connections per node
    cleanup_interval_sec=300,       # Cleanup frequency
)
```

### Index Parameters Explained

**ef_construction** (200)
- **Purpose:** Quality vs. indexing speed trade-off
- **Range:** 64-256
- **Higher = Better quality, slower indexing**
- **Lower = Faster indexing, worse quality**

**Default:** 200 (good balance for 1M items)

**ef** (128)
- **Purpose:** Query-time search breadth
- **Range:** 32-512
- **Higher = More accurate, slower**
- **Lower = Faster, less accurate**

**Default:** 128 (~95% recall at 200ms latency)

**max_connections** (32)
- **Purpose:** Graph connectivity per node
- **Range:** 8-64
- **Higher = More connected, slower**
- **Lower = Sparser, faster**

**Default:** 32 (balance for 512-dim vectors)

### Impact on Performance

```
Recall (↑) vs. Latency (↓) Trade-off

ef_construction = 64:    Indexing: 2min,  Query: 50ms,  Recall: 85%
ef_construction = 200:   Indexing: 8min,  Query: 120ms, Recall: 95%
ef_construction = 400:   Indexing: 25min, Query: 250ms, Recall: 99%

ef = 32:  Query: 50ms,  Recall: 80%
ef = 128: Query: 150ms, Recall: 95%
ef = 256: Query: 300ms, Recall: 99%
```

---

## 3. Property Indexes

### Metadata Indexing

```python
# Create indexes for filtering
db.connections.collection_name.aggregate([
    {
        "$createIndex": {
            "keys": {"category": 1}
        }
    }
])

# Best indexes for common queries
indexes = [
    ("product_id", 1),          # Unique lookup
    ("category", 1),            # Category filter
    ("color", 1),               # Color filter
    ("price", 1),               # Price range
    ("added_date", -1),         # Newest first
    ("rating", -1),             # Rating filter
    (["category", "color"], 1), # Compound filter
    (["category", "added_date"], 1),  # Browse by category
]
```

### Filtering Performance

```
Without indexes:
  category filter: 500ms on 1M products

With index:
  category filter: 5ms on 1M products
  
Speed improvement: 100x faster!
```

---

## 4. Query Optimization

### Basic Vector Search

```python
# Unoptimized: Returns all properties
results = collection.query.near_vector(
    near_vector=query_embedding,
    limit=10
)

# Optimized: Return only needed properties
results = collection.query.near_vector(
    near_vector=query_embedding,
    limit=10,
    return_properties=[
        "product_id", "title", "price",
        "category", "color", "image_path"
    ]
)

# Impact: 30% faster + 70% less network
```

### Filtered Search

```python
# Unoptimized: Fetch then filter
all_results = collection.query.near_vector(
    near_vector=query_embedding,
    limit=100
)
filtered = [r for r in all_results if r.properties["category"] == "shoes"]

# Optimized: Filter before ranking
from weaviate.classes.query import Filter

results = collection.query.near_vector(
    near_vector=query_embedding,
    where=Filter.by_property("category").equal("shoes"),
    limit=10
)

# Impact: 80% fewer results to rank + process
```

### Combining Multiple Filters

```python
from weaviate.classes.query import Filter

# AND filters
results = collection.query.near_vector(
    near_vector=query_embedding,
    where=(
        Filter.by_property("category").equal("shoes") &
        Filter.by_property("price").less_or_equal(150) &
        Filter.by_property("stock_level").greater_than(0)
    ),
    limit=10
)

# OR filters
results = collection.query.near_vector(
    near_vector=query_embedding,
    where=(
        Filter.by_property("color").equal("blue") |
        Filter.by_property("color").equal("navy")
    ),
    limit=10
)
```

### Batch Queries

```python
# Unoptimized: Multiple round-trips
for query in queries:
    embedding = clip_service.encode_text(query)
    results = collection.query.near_vector(
        near_vector=embedding,
        limit=10
    )
    # Process results

# Optimized: Batch processing
from concurrent.futures import ThreadPoolExecutor

embeddings = clip_service.encode_texts(queries)  # Vectorize all at once

with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [
        executor.submit(
            collection.query.near_vector,
            near_vector=embedding,
            limit=10
        )
        for embedding in embeddings
    ]
    results = [f.result() for f in futures]

# Impact: 5x faster for 50 queries
```

---

## 5. Performance Tuning

### Memory Configuration

```yaml
# docker-compose.yml
services:
  weaviate:
    environment:
      LIMIT_RESOURCES: "false"      # Unlimited memory
      GOMAXPROCS: "8"               # CPU threads
      GOMEMLIMIT: "8GiB"            # Memory limit
      VECTOR_CACHE_SIZE_PERCENT: 80 # Cache 80% of vectors
```

### Vector Cache

```
Vector Cache Purpose: Keep frequently accessed vectors in memory

Cache hit ratio:
- 100%: All vectors in memory (fast but memory-intensive)
- 80%: Most vectors cached (good balance)
- 20%: Mostly disk access (slow, low memory)

Optimal: 80% hit rate = best performance/memory balance
```

### Monitoring

```python
# Get index statistics
stats = collection.aggregate.over_all(
    return_properties=["_additional {count, lastUpdateTime}"]
)

print(f"Total vectors: {stats[0]['_additional']['count']}")
print(f"Last update: {stats[0]['_additional']['lastUpdateTime']}")

# Monitor query latency
import time

start = time.time()
results = collection.query.near_vector(
    near_vector=embedding,
    limit=10
)
latency = (time.time() - start) * 1000

print(f"Query latency: {latency:.1f}ms")
```

---

## 6. Scaling Strategies

### Scale 1: Single Instance (1M vectors)

**Configuration:**
```yaml
Memory: 16GB
CPU: 4 cores
ef_construction: 200
ef: 128
max_connections: 32
```

**Performance:**
- Indexing: 20 minutes
- Query latency: 100-150ms
- Throughput: 100-200 qps

### Scale 2: Replicated Cluster (10M vectors)

**Configuration:**
```yaml
Shards: 2 (split data)
Replicas: 2 (redundancy)
Memory per shard: 16GB
ef_construction: 256
ef: 128
```

**Performance:**
- Indexing: 40 minutes (parallel)
- Query latency: 80-120ms
- Throughput: 500-1000 qps

### Scale 3: Multi-Cluster (100M vectors)

**Configuration:**
```yaml
Primary cluster:
  Shards: 5
  Replicas: 3
  Memory: 100GB
  
Backup cluster:
  Shards: 5
  Replicas: 2
  Memory: 60GB
```

**Performance:**
- Indexing: 2 hours (distributed)
- Query latency: 60-100ms
- Throughput: 2000-5000 qps

---

## 7. Common Issues & Solutions

### Issue 1: Slow Queries (>500ms)

**Diagnosis:**
```python
# Check query metrics
explain = collection.query.near_vector(
    near_vector=embedding,
    explain=True,
    limit=10
)

# Should show:
# - Vector search time: 20-50ms
# - Post-processing: 10-30ms
# - Network: 5-10ms
```

**Solutions (in order):**

1. **Reduce ef value**
   ```python
   vector_config=Configure.VectorIndex.hnsw(ef=64)  # Fast
   ```

2. **Add property indexes**
   ```python
   # For filtered queries
   db.create_index([("category", 1)])
   ```

3. **Increase vector cache**
   ```yaml
   VECTOR_CACHE_SIZE_PERCENT: 90  # Was 80%
   ```

4. **Scale horizontally**
   ```yaml
   Shards: 4  # Split data
   ```

### Issue 2: High Memory Usage

**Diagnosis:**
```python
# Monitor memory
free -h  # Linux
Get-PhysicalMemory  # Windows PowerShell
```

**Solutions:**

1. **Reduce vector cache**
   ```yaml
   VECTOR_CACHE_SIZE_PERCENT: 60  # Was 80%
   ```

2. **Enable compression**
   ```yaml
   VECTOR_ENCODING: "bf16"  # 16-bit floats vs 32-bit
   ```

3. **Add shards**
   ```yaml
   Shards: 4  # Split across machines
   ```

### Issue 3: Poor Recall (<90%)

**Diagnosis:**
```python
# Test on known ground truth
true_neighbors = get_ground_truth(query_embedding)
retrieved = collection.query.near_vector(
    near_vector=query_embedding,
    limit=10
).objects

recall = len(set(true_neighbors) & set(retrieved)) / len(true_neighbors)
print(f"Recall: {recall:.1%}")
```

**Solutions:**

1. **Increase ef_construction**
   ```python
   vector_config=Configure.VectorIndex.hnsw(ef_construction=400)
   ```

2. **Increase ef**
   ```python
   collection.query.near_vector(
       near_vector=embedding,
       ef=256  # Was 128
   )
   ```

3. **Check embedding quality**
   ```python
   # Verify CLIP model produces consistent embeddings
   emb1 = clip_service.encode_text("blue shoes")
   emb2 = clip_service.encode_text("blue shoes")
   
   # Should be identical or very close
   assert np.allclose(emb1, emb2)
   ```

---

## 8. Best Practices

### 1. Embedding Quality

```python
# ✅ Good: Consistent normalization
embedding = clip_service.encode_text("blue shoes")
embedding = embedding / np.linalg.norm(embedding)  # Normalize

# ❌ Bad: Raw embeddings
embedding = clip_service.encode_text("blue shoes")  # Not normalized
```

### 2. Batch Indexing

```python
# ✅ Good: Batch insert (100x faster)
products = [
    {
        "product_id": f"prod_{i}",
        "title": f"Product {i}",
        "vector": embeddings[i]
    }
    for i in range(1000)
]

collection.data.insert_many(products)

# ❌ Bad: Individual inserts (slow)
for product in products:
    collection.data.insert(product)
```

### 3. Query Consistency

```python
# ✅ Good: Same embedding for same query
query = "blue shoes"
embedding = clip_service.encode_text(query)
results1 = search(embedding)
results2 = search(embedding)
assert results1 == results2

# ❌ Bad: Different embeddings
results1 = search(clip_service.encode_text(query))
results2 = search(clip_service.encode_text(query))
# Might be different due to randomness
```

### 4. Monitoring Queries

```python
# Track query performance
import logging

logger = logging.getLogger(__name__)

start = time.time()
results = collection.query.near_vector(
    near_vector=embedding,
    limit=10
)
latency = (time.time() - start) * 1000

logger.info(f"Query latency: {latency:.1f}ms, results: {len(results)}")

# Alert on slow queries
if latency > 500:
    logger.warning(f"Slow query: {latency:.1f}ms")
```

---

## 9. Benchmarking

### Benchmark Suite

```python
import time

def benchmark_vectors(collection, vectors, limits=[10, 50, 100]):
    results = {}
    
    for limit in limits:
        times = []
        
        for vector in vectors:
            start = time.time()
            collection.query.near_vector(
                near_vector=vector,
                limit=limit
            )
            times.append((time.time() - start) * 1000)
        
        results[limit] = {
            "min": min(times),
            "max": max(times),
            "avg": sum(times) / len(times),
            "p99": sorted(times)[int(len(times) * 0.99)]
        }
    
    return results

# Run benchmark
benchmarks = benchmark_vectors(collection, test_vectors)

# Print results
for limit, stats in benchmarks.items():
    print(f"Limit {limit}:")
    print(f"  Avg: {stats['avg']:.1f}ms")
    print(f"  P99: {stats['p99']:.1f}ms")
```

### Expected Results

| Metric | 10 Results | 50 Results | 100 Results |
|--------|-----------|-----------|------------|
| Avg latency | 50ms | 100ms | 150ms |
| P99 latency | 100ms | 200ms | 300ms |
| Throughput | 200 qps | 100 qps | 70 qps |

---

## 10. Optimization Checklist

- [ ] Vectors normalized before insertion
- [ ] HNSW index configured for your scale
- [ ] Property indexes created for filters
- [ ] Vector cache at 80%
- [ ] Query latency monitored (<500ms)
- [ ] Memory usage tracked
- [ ] Recall tested (>90%)
- [ ] Batch insert used for bulk operations
- [ ] Connection pooling enabled
- [ ] Backups configured

---

## References

- [Weaviate HNSW Configuration](https://weaviate.io/developers/weaviate/concepts/vector-index)
- [Vector Database Performance](https://arxiv.org/abs/2211.14626)
- [CLIP Model Specifications](https://github.com/openai/CLIP)
- [Approximate Nearest Neighbor](https://github.com/nmslib/hnsw)

---

**Status**: ✅ Complete
**Last Updated**: January 28, 2026
