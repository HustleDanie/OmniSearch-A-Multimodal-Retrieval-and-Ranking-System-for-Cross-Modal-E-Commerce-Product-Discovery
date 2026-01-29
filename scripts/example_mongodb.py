"""
Example usage of MongoDB client for managing products.
"""
from db import MongoDBClient, MongoDBConnection
from models import Product


def example_basic_usage():
    """Basic usage example."""
    # Create client and connect
    client = MongoDBClient()
    client.connect()
    
    try:
        # Create sample product
        product_data = {
            "product_id": "PROD-001",
            "title": "Blue Cotton T-Shirt",
            "description": "Comfortable cotton t-shirt in blue",
            "image_path": "/images/products/tshirt-001.jpg",
            "color": "blue",
            "category": "apparel"
        }
        
        # Insert product
        client.insert_product(product_data)
        
        # Fetch all products
        products = client.fetch_all_products()
        print(f"Total products: {len(products)}")
        
        # Fetch specific product
        product = client.fetch_product_by_id("PROD-001")
        print(f"Found product: {product['title']}")
        
    finally:
        client.disconnect()


def example_context_manager():
    """Example using context manager."""
    with MongoDBConnection() as client:
        # Insert multiple products
        products = [
            {
                "product_id": "PROD-002",
                "title": "Red Sneakers",
                "description": "Athletic sneakers in red",
                "image_path": "/images/products/sneakers-002.jpg",
                "color": "red",
                "category": "footwear"
            },
            {
                "product_id": "PROD-003",
                "title": "Green Backpack",
                "description": "Durable backpack in green",
                "image_path": "/images/products/backpack-003.jpg",
                "color": "green",
                "category": "accessories"
            }
        ]
        
        client.insert_products(products)
        
        # Fetch by category
        footwear = client.fetch_products_by_category("footwear")
        print(f"Footwear products: {len(footwear)}")


def example_with_pydantic():
    """Example using Pydantic models for validation."""
    with MongoDBConnection() as client:
        # Create validated product using Pydantic
        product = Product(
            product_id="PROD-004",
            title="Black Leather Jacket",
            description="Premium leather jacket in black",
            image_path="/images/products/jacket-004.jpg",
            color="black",
            category="apparel"
        )
        
        # Convert to dict and insert
        client.insert_product(product.model_dump())
        
        # Fetch and validate
        fetched = client.fetch_product_by_id("PROD-004")
        if fetched:
            validated_product = Product(**fetched)
            print(f"Validated: {validated_product.title}")


if __name__ == "__main__":
    print("=== Basic Usage ===")
    example_basic_usage()
    
    print("\n=== Context Manager ===")
    example_context_manager()
    
    print("\n=== With Pydantic ===")
    example_with_pydantic()
