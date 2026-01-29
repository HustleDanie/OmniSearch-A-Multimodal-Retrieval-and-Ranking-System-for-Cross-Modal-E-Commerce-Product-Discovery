"""
Example usage of Weaviate client for product vector storage.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import WeaviateClient, WeaviateConnection
from services import get_clip_service
import numpy as np


def example_setup_schema():
    """Example: Create Product schema in Weaviate."""
    print("=== Setup Weaviate Schema ===\n")
    
    # Connect and create schema
    with WeaviateConnection() as client:
        # Create Product collection with manual vectorization
        # CLIP ViT-B/32 produces 512-dimensional vectors
        client.create_product_schema(vector_dimension=512)
        
        # Get collection info
        info = client.get_collection_info()
        print(f"\nCollection info: {info}")


def example_insert_with_vectors():
    """Example: Insert products with CLIP embeddings."""
    print("\n=== Insert Products with Vectors ===\n")
    
    # Initialize CLIP service
    clip_service = get_clip_service()
    
    with WeaviateConnection() as client:
        # Sample product
        product = {
            "product_id": "PROD-001",
            "title": "Blue Cotton T-Shirt",
            "description": "Comfortable cotton t-shirt in blue",
            "color": "blue",
            "category": "apparel",
            "image_path": "/images/products/tshirt-001.jpg"
        }
        
        # Generate embedding from text
        text = f"{product['title']}. {product['description']}"
        vector = clip_service.embed_text(text)
        
        # Insert product with vector
        uuid = client.insert_product_with_vector(product, vector)
        print(f"Inserted product with UUID: {uuid}")
        
        # Check collection
        info = client.get_collection_info()
        print(f"Total objects in collection: {info['total_objects']}")


def example_batch_insert():
    """Example: Batch insert multiple products."""
    print("\n=== Batch Insert Products ===\n")
    
    clip_service = get_clip_service()
    
    # Sample products
    products = [
        {
            "product_id": "PROD-002",
            "title": "Red Sneakers",
            "description": "Athletic sneakers in red",
            "color": "red",
            "category": "footwear",
            "image_path": "/images/products/sneakers-002.jpg"
        },
        {
            "product_id": "PROD-003",
            "title": "Green Backpack",
            "description": "Durable backpack in green",
            "color": "green",
            "category": "accessories",
            "image_path": "/images/products/backpack-003.jpg"
        },
        {
            "product_id": "PROD-004",
            "title": "Black Leather Jacket",
            "description": "Premium leather jacket in black",
            "color": "black",
            "category": "apparel",
            "image_path": "/images/products/jacket-004.jpg"
        }
    ]
    
    # Generate embeddings in batch
    texts = [f"{p['title']}. {p['description']}" for p in products]
    vectors = clip_service.embed_texts_batch(texts)
    
    with WeaviateConnection() as client:
        # Batch insert
        uuids = client.insert_products_batch(products, vectors)
        print(f"Inserted {len(uuids)} products")
        
        # Check collection
        info = client.get_collection_info()
        print(f"Total objects in collection: {info['total_objects']}")


def example_vector_search():
    """Example: Search products using text query."""
    print("\n=== Vector Search ===\n")
    
    clip_service = get_clip_service()
    
    # Query
    query_text = "red athletic shoes"
    print(f"Searching for: '{query_text}'\n")
    
    # Generate query vector
    query_vector = clip_service.embed_text(query_text)
    
    with WeaviateConnection() as client:
        # Search
        results = client.search_by_vector(query_vector, limit=5)
        
        print(f"Found {len(results)} results:\n")
        for i, result in enumerate(results, 1):
            props = result["properties"]
            similarity = result["similarity"]
            print(f"{i}. {props['title']}")
            print(f"   Category: {props['category']} | Color: {props['color']}")
            print(f"   Similarity: {similarity:.4f}")
            print()


def example_cleanup():
    """Example: Delete collection."""
    print("\n=== Cleanup ===\n")
    
    with WeaviateConnection() as client:
        client.delete_collection()


if __name__ == "__main__":
    # Setup schema
    example_setup_schema()
    
    # Insert products
    example_insert_with_vectors()
    example_batch_insert()
    
    # Search
    example_vector_search()
    
    # Cleanup (optional - uncomment to delete collection)
    # example_cleanup()
    
    print("\n✓ All examples completed!")
