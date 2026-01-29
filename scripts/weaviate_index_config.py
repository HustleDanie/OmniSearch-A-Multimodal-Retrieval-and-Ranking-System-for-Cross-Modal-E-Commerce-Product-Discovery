"""
Weaviate Index Configuration Examples

Practical code snippets for configuring and benchmarking HNSW and IVF indexes.
"""

import weaviate
from weaviate.classes.config import Configure, Property, DataType, IndexType, VectorIndexConfig, IVFConfig
import time
import statistics
from typing import List, Dict
import numpy as np


# ============================================================================
# 1. SCHEMA DEFINITIONS
# ============================================================================

class WeaviateSchemas:
    """Collection of Weaviate schema definitions"""

    @staticmethod
    def hnsw_high_recall():
        """HNSW optimized for high recall"""
        return {
            "class": "DocumentHNSWRecall",
            "vectorIndexType": "hnsw",
            "vectorIndexConfig": {
                "ef": 128,              # Search parameter
                "efConstruction": 200,  # Build parameter
                "maxConnections": 32,   # Graph connectivity
                "dynamicEfMin": 100,
                "dynamicEfMax": 500,
            },
            "properties": [
                {
                    "name": "content",
                    "dataType": ["text"],
                    "vectorizePropertyName": True,
                },
                {
                    "name": "title",
                    "dataType": ["string"],
                },
            ]
        }

    @staticmethod
    def hnsw_speed_optimized():
        """HNSW optimized for query speed"""
        return {
            "class": "DocumentHNSWSpeed",
            "vectorIndexType": "hnsw",
            "vectorIndexConfig": {
                "ef": 64,               # Lower search parameter
                "efConstruction": 100,  # Lower build parameter
                "maxConnections": 16,   # Fewer connections
                "dynamicEfMin": 50,
                "dynamicEfMax": 200,
            },
            "properties": [
                {
                    "name": "content",
                    "dataType": ["text"],
                },
            ]
        }

    @staticmethod
    def hnsw_memory_optimized():
        """HNSW with minimum memory footprint"""
        return {
            "class": "DocumentHNSWMemory",
            "vectorIndexType": "hnsw",
            "vectorIndexConfig": {
                "ef": 96,
                "efConstruction": 150,
                "maxConnections": 12,   # Minimum connections
                "dynamicEfMin": 80,
                "dynamicEfMax": 300,
            },
            "properties": [
                {
                    "name": "content",
                    "dataType": ["text"],
                },
            ]
        }

    @staticmethod
    def ivf_balanced():
        """IVF with balanced recall and speed"""
        return {
            "class": "DocumentIVFBalanced",
            "vectorIndexType": "ivf",
            "vectorIndexConfig": {
                "nlist": 1024,          # Number of clusters
                "nprobe": 20,           # Clusters to search
            },
            "properties": [
                {
                    "name": "content",
                    "dataType": ["text"],
                },
            ]
        }

    @staticmethod
    def ivf_high_recall():
        """IVF optimized for high recall"""
        return {
            "class": "DocumentIVFRecall",
            "vectorIndexType": "ivf",
            "vectorIndexConfig": {
                "nlist": 1024,
                "nprobe": 256,          # Search 25% of clusters
                "hnswEf": 300,          # HNSW secondary level
            },
            "properties": [
                {
                    "name": "content",
                    "dataType": ["text"],
                },
            ]
        }

    @staticmethod
    def ivf_large_scale():
        """IVF for 10M+ vectors"""
        return {
            "class": "DocumentIVFScale",
            "vectorIndexType": "ivf",
            "vectorIndexConfig": {
                "nlist": 10000,         # √10M
                "nprobe": 64,           # 0.6% of clusters
                "hnswEf": 200,
            },
            "properties": [
                {
                    "name": "content",
                    "dataType": ["text"],
                },
            ]
        }


# ============================================================================
# 2. SCHEMA CREATION
# ============================================================================

class IndexManager:
    """Manage index creation and configuration"""

    def __init__(self, weaviate_url: str = "http://localhost:8080"):
        self.client = weaviate.connect_to_local()

    def create_collection_from_schema(self, schema: Dict) -> bool:
        """Create a Weaviate collection from schema"""
        try:
            self.client.collections.create_from_dict(schema)
            print(f"✓ Created collection: {schema['class']}")
            return True
        except Exception as e:
            print(f"✗ Failed to create {schema['class']}: {e}")
            return False

    def delete_collection(self, class_name: str) -> bool:
        """Delete a collection"""
        try:
            self.client.collections.delete(class_name)
            print(f"✓ Deleted collection: {class_name}")
            return True
        except Exception as e:
            print(f"✗ Failed to delete {class_name}: {e}")
            return False

    def get_index_config(self, class_name: str) -> Dict:
        """Retrieve current index configuration"""
        try:
            collection = self.client.collections.get(class_name)
            config = collection.config
            return {
                "vector_index_type": config.vector_index_type,
                "vector_index_config": config.vector_index_config,
            }
        except Exception as e:
            print(f"✗ Failed to get config for {class_name}: {e}")
            return {}

    def print_collection_stats(self, class_name: str):
        """Print collection statistics"""
        try:
            collection = self.client.collections.get(class_name)
            response = collection.aggregate.over_all(
                group_by=None,
            )
            count = response.total_count
            
            config = collection.config
            index_type = config.vector_index_type
            
            print(f"\n{'='*60}")
            print(f"Collection: {class_name}")
            print(f"{'='*60}")
            print(f"Vector Index Type: {index_type}")
            print(f"Object Count: {count:,}")
            print(f"Index Config: {config.vector_index_config}")
            print(f"{'='*60}\n")
        except Exception as e:
            print(f"✗ Failed to get stats for {class_name}: {e}")


# ============================================================================
# 3. PERFORMANCE BENCHMARKING
# ============================================================================

class IndexBenchmark:
    """Benchmark index performance"""

    def __init__(self, client):
        self.client = client
        self.results = {}

    def benchmark_query_speed(
        self,
        class_name: str,
        test_vectors: List[List[float]],
        num_iterations: int = 100,
        limit: int = 10,
    ) -> Dict:
        """
        Benchmark query speed for a collection
        
        Returns:
            Dict with timing statistics
        """
        query_times = []
        recall_positions = []
        
        try:
            collection = self.client.collections.get(class_name)
            
            # Use first test vector for all queries
            test_vector = test_vectors[0]
            
            for i in range(num_iterations):
                start = time.perf_counter()
                
                results = collection.query.near_vector(
                    near_vector=test_vector,
                    limit=limit,
                ).objects
                
                elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
                query_times.append(elapsed)
                
                if results:
                    recall_positions.append(len(results))
            
            stats = {
                "class": class_name,
                "avg_ms": statistics.mean(query_times),
                "median_ms": statistics.median(query_times),
                "p99_ms": sorted(query_times)[int(num_iterations * 0.99)],
                "p95_ms": sorted(query_times)[int(num_iterations * 0.95)],
                "min_ms": min(query_times),
                "max_ms": max(query_times),
                "stdev_ms": statistics.stdev(query_times) if len(query_times) > 1 else 0,
            }
            
            self.results[class_name] = stats
            return stats
            
        except Exception as e:
            print(f"✗ Benchmark failed for {class_name}: {e}")
            return {}

    def benchmark_build_speed(
        self,
        class_name: str,
        vectors: List[List[float]],
        batch_size: int = 100,
    ) -> Dict:
        """
        Benchmark build/insertion speed
        
        Returns:
            Dict with timing statistics
        """
        try:
            collection = self.client.collections.get(class_name)
            
            start = time.perf_counter()
            inserted = 0
            
            with collection.batch.dynamic() as batch:
                for idx, vector in enumerate(vectors):
                    batch.add_object(
                        properties={
                            "content": f"Document {idx}",
                            "title": f"Title {idx}",
                        },
                        vector=vector,
                    )
                    inserted += 1
            
            elapsed = (time.perf_counter() - start)  # seconds
            
            stats = {
                "class": class_name,
                "total_vectors": inserted,
                "total_seconds": elapsed,
                "vectors_per_second": inserted / elapsed if elapsed > 0 else 0,
            }
            
            return stats
            
        except Exception as e:
            print(f"✗ Build benchmark failed for {class_name}: {e}")
            return {}

    def compare_indexes(self, class_names: List[str]) -> None:
        """Print comparison of benchmark results"""
        print("\n" + "="*80)
        print("BENCHMARK COMPARISON")
        print("="*80)
        print(f"{'Collection':<25} {'Avg (ms)':<12} {'P99 (ms)':<12} {'StDev':<10}")
        print("-"*80)
        
        for class_name in class_names:
            if class_name in self.results:
                stats = self.results[class_name]
                print(f"{stats['class']:<25} {stats['avg_ms']:<12.2f} "
                      f"{stats['p99_ms']:<12.2f} {stats['stdev_ms']:<10.2f}")
        
        print("="*80 + "\n")


# ============================================================================
# 4. PRACTICAL EXAMPLES
# ============================================================================

class ConfigurationExamples:
    """Real-world configuration examples"""

    @staticmethod
    def ecommerce_product_search() -> Dict:
        """
        E-commerce product search
        - 1M products
        - Recall critical
        - < 50ms latency acceptable
        """
        return {
            "class": "Product",
            "description": "E-commerce products with high recall requirements",
            "vectorIndexType": "hnsw",
            "vectorIndexConfig": {
                "ef": 128,
                "efConstruction": 200,
                "maxConnections": 32,
                "dynamicEfMin": 100,
                "dynamicEfMax": 500,
            },
            "properties": [
                {"name": "title", "dataType": ["text"]},
                {"name": "description", "dataType": ["text"]},
                {"name": "category", "dataType": ["string"]},
                {"name": "price", "dataType": ["number"]},
            ]
        }

    @staticmethod
    def realtime_recommendations() -> Dict:
        """
        Real-time recommendation engine
        - 10M user profiles
        - < 10ms latency critical
        - Memory-constrained
        """
        return {
            "class": "UserProfile",
            "description": "User profiles for real-time recommendations",
            "vectorIndexType": "ivf",
            "vectorIndexConfig": {
                "nlist": 3162,  # √10M
                "nprobe": 32,   # 1% of clusters
                "hnswEf": 150,
            },
            "properties": [
                {"name": "user_id", "dataType": ["string"]},
                {"name": "behavior", "dataType": ["text"]},
                {"name": "preferences", "dataType": ["string"]},
            ]
        }

    @staticmethod
    def legal_document_archive() -> Dict:
        """
        Legal document archive
        - 100M documents
        - Recall > 95% critical
        - Batch queries acceptable
        """
        return {
            "class": "LegalDocument",
            "description": "Legal document archive with high recall",
            "vectorIndexType": "ivf",
            "vectorIndexConfig": {
                "nlist": 10000,
                "nprobe": 512,      # High nprobe for recall
                "hnswEf": 300,
            },
            "properties": [
                {"name": "text", "dataType": ["text"]},
                {"name": "case_number", "dataType": ["string"]},
                {"name": "date", "dataType": ["string"]},
            ]
        }

    @staticmethod
    def mobile_on_device_search() -> Dict:
        """
        Mobile on-device search
        - 10K vectors max
        - Memory critical (< 50MB)
        - Decent recall needed
        """
        return {
            "class": "LocalDocument",
            "description": "On-device search with minimal memory",
            "vectorIndexType": "hnsw",
            "vectorIndexConfig": {
                "ef": 80,           # Reduced search
                "efConstruction": 100,
                "maxConnections": 8,  # Minimal connections
                "dynamicEfMin": 40,
                "dynamicEfMax": 150,
                "flatSearchCutoff": 10000,  # Use linear for small sets
            },
            "properties": [
                {"name": "text", "dataType": ["text"]},
            ]
        }


# ============================================================================
# 5. PRACTICAL WORKFLOW
# ============================================================================

def complete_workflow_example():
    """
    Complete workflow: create -> insert -> benchmark -> compare
    """
    
    print("Starting Weaviate Index Configuration Workflow...\n")
    
    # Initialize manager
    manager = IndexManager()
    
    # 1. Create collections with different configurations
    print("1. Creating collections with different index types...")
    schemas = [
        WeaviateSchemas.hnsw_high_recall(),
        WeaviateSchemas.hnsw_speed_optimized(),
        WeaviateSchemas.ivf_balanced(),
    ]
    
    for schema in schemas:
        manager.create_collection_from_schema(schema)
        time.sleep(0.5)
    
    # 2. Generate test vectors
    print("\n2. Generating 1000 test vectors (768-dim)...")
    np.random.seed(42)
    test_vectors = np.random.randn(1000, 768).astype(np.float32)
    
    # 3. Insert vectors into each collection
    print("\n3. Inserting vectors into collections...")
    benchmark = IndexBenchmark(manager.client)
    
    collection_names = [
        "DocumentHNSWRecall",
        "DocumentHNSWSpeed",
        "DocumentIVFBalanced",
    ]
    
    for class_name in collection_names:
        print(f"\n   Inserting into {class_name}...")
        build_stats = benchmark.benchmark_build_speed(
            class_name,
            test_vectors.tolist(),
        )
        if build_stats:
            print(f"   ✓ Inserted {build_stats['total_vectors']} vectors "
                  f"in {build_stats['total_seconds']:.2f}s "
                  f"({build_stats['vectors_per_second']:.0f} v/s)")
    
    # 4. Benchmark query speed
    print("\n4. Benchmarking query speed (100 iterations)...")
    for class_name in collection_names:
        print(f"\n   Benchmarking {class_name}...")
        query_stats = benchmark.benchmark_query_speed(
            class_name,
            test_vectors.tolist(),
            num_iterations=100,
        )
        if query_stats:
            print(f"   ✓ Avg: {query_stats['avg_ms']:.2f}ms | "
                  f"P99: {query_stats['p99_ms']:.2f}ms | "
                  f"StDev: {query_stats['stdev_ms']:.2f}ms")
    
    # 5. Print comparison
    benchmark.compare_indexes(collection_names)
    
    # 6. Print collection stats
    print("\n5. Collection Statistics:")
    for class_name in collection_names:
        manager.print_collection_stats(class_name)


# ============================================================================
# 6. HELPER FUNCTIONS
# ============================================================================

def calculate_recommended_nlist(dataset_size: int) -> int:
    """
    Calculate recommended nlist for IVF based on dataset size
    Formula: √N (where N = dataset size)
    """
    import math
    return max(32, min(65536, int(math.sqrt(dataset_size))))


def calculate_recommended_nprobe(nlist: int, target_recall: float) -> int:
    """
    Calculate recommended nprobe based on target recall
    
    target_recall: 0.0-1.0 (e.g., 0.9 for 90%)
    """
    # Empirical relationship: more recall = higher nprobe
    nprobe_ratio = 0.01 + (target_recall - 0.8) * 0.15
    return max(1, min(nlist, int(nlist * nprobe_ratio)))


def estimate_memory_usage(
    num_vectors: int,
    vector_dim: int,
    index_type: str = "hnsw",
    max_connections: int = 32,
) -> Dict:
    """
    Estimate memory usage for index
    """
    # Vector storage: 4 bytes per float (32-bit)
    vector_memory_gb = (num_vectors * vector_dim * 4) / (1024**3)
    
    if index_type == "hnsw":
        # Graph overhead: max_connections * pointer_size * num_vectors
        graph_memory_gb = (num_vectors * max_connections * 8) / (1024**3)
        overhead_gb = 0.05  # 5% overhead
        total_gb = vector_memory_gb + graph_memory_gb + overhead_gb
    else:  # IVF
        # Cluster assignments: 4 bytes per vector
        assignment_memory_gb = (num_vectors * 4) / (1024**3)
        overhead_gb = 0.01  # 1% overhead
        total_gb = vector_memory_gb + assignment_memory_gb + overhead_gb
    
    return {
        "vector_storage_gb": vector_memory_gb,
        "graph_or_assignment_gb": graph_memory_gb if index_type == "hnsw" else assignment_memory_gb,
        "overhead_gb": overhead_gb,
        "total_estimated_gb": total_gb,
    }


# ============================================================================
# 7. MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    # Example: Calculate memory for 1M vectors
    print("Memory Estimation Example (1M vectors, 384-dim):\n")
    
    hnsw_memory = estimate_memory_usage(1_000_000, 384, "hnsw", 32)
    print("HNSW Memory:")
    for key, value in hnsw_memory.items():
        print(f"  {key}: {value:.2f} GB")
    
    print()
    
    ivf_memory = estimate_memory_usage(1_000_000, 384, "ivf")
    print("IVF Memory:")
    for key, value in ivf_memory.items():
        print(f"  {key}: {value:.2f} GB")
    
    # Example: Calculate IVF parameters
    print("\n\nIVF Parameter Recommendation (10M vectors):\n")
    dataset_size = 10_000_000
    nlist = calculate_recommended_nlist(dataset_size)
    print(f"Recommended nlist: {nlist:,}")
    
    for recall in [0.80, 0.85, 0.90, 0.95]:
        nprobe = calculate_recommended_nprobe(nlist, recall)
        print(f"  Target {recall*100:.0f}% recall: nprobe = {nprobe:,} "
              f"({nprobe/nlist*100:.1f}% of clusters)")
    
    # Uncomment to run full workflow (requires running Weaviate instance)
    # complete_workflow_example()
