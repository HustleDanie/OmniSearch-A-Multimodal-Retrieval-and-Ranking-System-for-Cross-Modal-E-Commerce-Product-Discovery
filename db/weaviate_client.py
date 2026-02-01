"""
Weaviate Vector Database Client for Product Search.
Handles connection, schema creation, and vector operations.
"""
import weaviate
from weaviate.classes.config import Configure, Property, DataType, VectorDistances
from weaviate.classes.query import Filter
import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import numpy as np

load_dotenv()


class WeaviateClient:
    """Client for managing product vectors in Weaviate."""
    
    def __init__(self, url: Optional[str] = None):
        """
        Initialize Weaviate client.
        
        Args:
            url: Weaviate instance URL. If None, uses WEAVIATE_URL from environment.
        """
        self.url = url or os.getenv("WEAVIATE_URL", "http://localhost:8080")
        self.client: Optional[weaviate.WeaviateClient] = None
        self.collection_name = "Product"
    
    def connect(self) -> None:
        """Establish connection to Weaviate."""
        try:
            # Extract host from URL (remove http/https protocol)
            host = self.url.replace("http://", "").replace("https://", "").split(":")[0]
            
            self.client = weaviate.connect_to_custom(
                http_host=host,
                http_port=8080,
                http_secure=False,
                grpc_host=host,
                grpc_port=50051,
                grpc_secure=False
            )
            
            # Test connection
            if self.client.is_ready():
                print(f"✓ Connected to Weaviate at {self.url}")
            else:
                raise ConnectionError("Weaviate is not ready")
                
        except Exception as e:
            print(f"✗ Failed to connect to Weaviate: {e}")
            raise
    
    def disconnect(self) -> None:
        """Close Weaviate connection."""
        if self.client:
            self.client.close()
            print("✓ Disconnected from Weaviate")
    
    def create_product_schema(self, vector_dimension: int = 512) -> None:
        """
        Create Product class/collection in Weaviate with manual vectorization.
        
        Args:
            vector_dimension: Dimension of the embedding vectors (default: 512 for CLIP ViT-B/32)
        """
        if not self.client:
            raise RuntimeError("Not connected to Weaviate. Call connect() first.")
        
        try:
            # Check if collection already exists
            if self.client.collections.exists(self.collection_name):
                print(f"Collection '{self.collection_name}' already exists")
                return
            
            # Create collection with manual vectorization (no built-in vectorizer)
            self.client.collections.create(
                name=self.collection_name,
                description="Product catalog with CLIP embeddings for multimodal search",
                
                # Disable built-in vectorization - we'll provide vectors manually
                vectorizer_config=None,
                
                # Configure vector index for similarity search
                vector_index_config=Configure.VectorIndex.hnsw(
                    distance_metric=VectorDistances.COSINE,  # Cosine similarity for normalized vectors
                    ef_construction=128,        # Higher = better quality, slower indexing
                    ef=64,                     # Higher = better search quality
                    max_connections=64         # Connections per layer
                ),
                
                # Define properties/fields
                properties=[
                    Property(
                        name="product_id",
                        data_type=DataType.TEXT,
                        description="Unique product identifier",
                        skip_vectorization=True,
                        index_filterable=True,
                        index_searchable=False
                    ),
                    Property(
                        name="title",
                        data_type=DataType.TEXT,
                        description="Product title",
                        skip_vectorization=True,
                        index_filterable=True,
                        index_searchable=True
                    ),
                    Property(
                        name="description",
                        data_type=DataType.TEXT,
                        description="Product description",
                        skip_vectorization=True,
                        index_filterable=False,
                        index_searchable=True
                    ),
                    Property(
                        name="color",
                        data_type=DataType.TEXT,
                        description="Product color",
                        skip_vectorization=True,
                        index_filterable=True,
                        index_searchable=False
                    ),
                    Property(
                        name="category",
                        data_type=DataType.TEXT,
                        description="Product category",
                        skip_vectorization=True,
                        index_filterable=True,
                        index_searchable=False
                    ),
                    Property(
                        name="image_path",
                        data_type=DataType.TEXT,
                        description="Path to product image",
                        skip_vectorization=True,
                        index_filterable=False,
                        index_searchable=False
                    )
                ]
            )
            
            print(f"✓ Created collection '{self.collection_name}' with manual vectorization")
            print(f"  Vector dimension: {vector_dimension}")
            print(f"  Distance metric: cosine")
            print(f"  Properties: product_id, title, description, color, category, image_path")
            
        except Exception as e:
            print(f"✗ Failed to create schema: {e}")
            raise
    
    def insert_product_with_vector(self, properties: Dict[str, Any], 
                                   vector: np.ndarray) -> str:
        """
        Insert a single product with its embedding vector.
        
        Args:
            properties: Dictionary with product properties
            vector: Embedding vector (numpy array)
            
        Returns:
            UUID of the inserted object
        """
        if not self.client:
            raise RuntimeError("Not connected to Weaviate. Call connect() first.")
        
        try:
            collection = self.client.collections.get(self.collection_name)
            
            # Convert numpy array to list if needed
            if isinstance(vector, np.ndarray):
                vector = vector.tolist()
            
            # Insert object with vector
            uuid = collection.data.insert(
                properties=properties,
                vector=vector
            )
            
            return str(uuid)
            
        except Exception as e:
            print(f"✗ Failed to insert product: {e}")
            raise
    
    def insert_products_batch(self, products: List[Dict[str, Any]], 
                             vectors: np.ndarray) -> List[str]:
        """
        Insert multiple products with their vectors efficiently.
        
        Args:
            products: List of product property dictionaries
            vectors: Array of embedding vectors (shape: [n_products, embedding_dim])
            
        Returns:
            List of UUIDs for inserted objects
        """
        if not self.client:
            raise RuntimeError("Not connected to Weaviate. Call connect() first.")
        
        if len(products) != len(vectors):
            raise ValueError(f"Mismatch: {len(products)} products but {len(vectors)} vectors")
        
        try:
            collection = self.client.collections.get(self.collection_name)
            uuids = []
            
            # Use batch insert for efficiency
            with collection.batch.dynamic() as batch:
                for product, vector in zip(products, vectors):
                    # Convert numpy array to list
                    vector_list = vector.tolist() if isinstance(vector, np.ndarray) else vector
                    
                    uuid = batch.add_object(
                        properties=product,
                        vector=vector_list
                    )
                    uuids.append(str(uuid))
            
            print(f"✓ Inserted {len(products)} products with vectors")
            return uuids
            
        except Exception as e:
            print(f"✗ Failed to batch insert products: {e}")
            raise
    
    def delete_collection(self) -> None:
        """Delete the Product collection."""
        if not self.client:
            raise RuntimeError("Not connected to Weaviate. Call connect() first.")
        
        try:
            if self.client.collections.exists(self.collection_name):
                self.client.collections.delete(self.collection_name)
                print(f"✓ Deleted collection '{self.collection_name}'")
            else:
                print(f"Collection '{self.collection_name}' does not exist")
                
        except Exception as e:
            print(f"✗ Failed to delete collection: {e}")
            raise
    
    def get_collection_info(self) -> Dict[str, Any]:
        """
        Get information about the Product collection.
        
        Returns:
            Dictionary with collection metadata
        """
        if not self.client:
            raise RuntimeError("Not connected to Weaviate. Call connect() first.")
        
        try:
            if not self.client.collections.exists(self.collection_name):
                return {"exists": False}
            
            collection = self.client.collections.get(self.collection_name)
            
            # Get object count
            result = collection.aggregate.over_all(total_count=True)
            
            return {
                "exists": True,
                "name": self.collection_name,
                "total_objects": result.total_count,
            }
            
        except Exception as e:
            print(f"✗ Failed to get collection info: {e}")
            raise
    
    def search_by_vector(self, query_vector: np.ndarray, 
                        limit: int = 10,
                        filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search for products using a query vector.
        
        Args:
            query_vector: Query embedding vector
            limit: Maximum number of results to return
            filters: Optional filters (e.g., {"category": "apparel"})
            
        Returns:
            List of matching products with similarity scores
        """
        if not self.client:
            raise RuntimeError("Not connected to Weaviate. Call connect() first.")
        
        try:
            collection = self.client.collections.get(self.collection_name)
            
            # Convert numpy array to list
            vector_list = query_vector.tolist() if isinstance(query_vector, np.ndarray) else query_vector
            
            # Build where filter if provided
            where_filter = None
            if filters:
                conditions = []
                category = filters.get("category")
                color = filters.get("color")
                if category is not None:
                    conditions.append(Filter.by_property("category").equal(category))
                if color is not None:
                    conditions.append(Filter.by_property("color").equal(color))
                if conditions:
                    # Chain with AND
                    where_filter = conditions[0]
                    for cond in conditions[1:]:
                        where_filter = where_filter & cond

            # Perform vector search with optional filters
            response = collection.query.near_vector(
                near_vector=vector_list,
                limit=limit,
                filters=where_filter,
                return_metadata=["distance"]
            )
            
            # Format results
            results = []
            for obj in response.objects:
                result = {
                    "uuid": str(obj.uuid),
                    "properties": obj.properties,
                    "distance": obj.metadata.distance,
                    "similarity": 1 - obj.metadata.distance  # Convert distance to similarity
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            print(f"✗ Failed to search: {e}")
            raise


# Context manager support
class WeaviateConnection:
    """Context manager for Weaviate connections."""
    
    def __init__(self, url: Optional[str] = None):
        self.client = WeaviateClient(url)
    
    def __enter__(self) -> WeaviateClient:
        self.client.connect()
        return self.client
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.disconnect()
        return False
