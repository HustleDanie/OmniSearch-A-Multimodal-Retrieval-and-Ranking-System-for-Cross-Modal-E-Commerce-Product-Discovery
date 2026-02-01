#!/usr/bin/env python3
"""Add more sample products to the database for better search results."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import WeaviateConnection
from services import get_clip_service
import numpy as np

# Sample products with diverse attributes
SAMPLE_PRODUCTS = [
    {
        "product_id": "prod_001",
        "title": "Black Leather Jacket",
        "description": "Classic black leather jacket for men and women",
        "color": "black",
        "category": "apparel",
        "image_path": "/images/black-jacket.jpg"
    },
    {
        "product_id": "prod_002",
        "title": "Red Sneakers",
        "description": "Comfortable red running sneakers with cushioned sole",
        "color": "red",
        "category": "footwear",
        "image_path": "/images/red-sneakers.jpg"
    },
    {
        "product_id": "prod_003",
        "title": "Blue Cotton T-Shirt",
        "description": "Soft blue cotton t-shirt perfect for casual wear",
        "color": "blue",
        "category": "apparel",
        "image_path": "/images/blue-tshirt.jpg"
    },
    {
        "product_id": "prod_004",
        "title": "Green Backpack",
        "description": "Durable green backpack for hiking and travel",
        "color": "green",
        "category": "accessories",
        "image_path": "/images/green-backpack.jpg"
    },
    # New products for better search diversity
    {
        "product_id": "prod_005",
        "title": "Black Jeep Model",
        "description": "Detailed die-cast model of a black jeep SUV vehicle",
        "color": "black",
        "category": "toys",
        "image_path": "/images/black-jeep.jpg"
    },
    {
        "product_id": "prod_006",
        "title": "Black Jeep Toy Car",
        "description": "1:24 scale black jeep toy vehicle with working wheels",
        "color": "black",
        "category": "toys",
        "image_path": "/images/black-jeep-toy.jpg"
    },
    {
        "product_id": "prod_007",
        "title": "Green Piano Keyboard",
        "description": "Electronic green piano keyboard with 61 keys and built-in sounds",
        "color": "green",
        "category": "musical_instruments",
        "image_path": "/images/green-piano.jpg"
    },
    {
        "product_id": "prod_008",
        "title": "Black Grand Piano",
        "description": "Professional black grand piano with full 88-key keyboard",
        "color": "black",
        "category": "musical_instruments",
        "image_path": "/images/black-piano.jpg"
    },
    {
        "product_id": "prod_009",
        "title": "Green Dress",
        "description": "Elegant green silk dress for formal occasions",
        "color": "green",
        "category": "apparel",
        "image_path": "/images/green-dress.jpg"
    },
    {
        "product_id": "prod_010",
        "title": "Red Leather Handbag",
        "description": "Stylish red leather handbag with multiple compartments",
        "color": "red",
        "category": "accessories",
        "image_path": "/images/red-handbag.jpg"
    },
]

def main():
    clip_service = get_clip_service()
    
    with WeaviateConnection() as client:
        # Clear existing data
        print("Clearing existing products...")
        try:
            client.delete_collection()
            print("✓ Deleted old collection")
        except Exception as e:
            print(f"Note: {e}")
        
        # Create schema
        print("Creating schema...")
        client.create_product_schema()
        
        # Add products
        print(f"\nAdding {len(SAMPLE_PRODUCTS)} products...")
        for i, product in enumerate(SAMPLE_PRODUCTS, 1):
            # Generate embedding from title and description
            text_to_embed = f"{product['title']}. {product['description']}"
            embedding = clip_service.embed_text(text_to_embed)
            
            # Insert product
            uuid = client.insert_product_with_vector(
                properties={
                    "product_id": product["product_id"],
                    "title": product["title"],
                    "description": product["description"],
                    "color": product["color"],
                    "category": product["category"],
                    "image_path": product["image_path"]
                },
                vector=embedding
            )
            
            print(f"  {i}. {product['title']} ({product['color']} {product['category']})")
        
        # Verify
        info = client.get_collection_info()
        print(f"\n✓ Successfully added {info['total_objects']} products to the database!")

if __name__ == "__main__":
    main()
