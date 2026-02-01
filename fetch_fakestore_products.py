#!/usr/bin/env python3
"""
Fetch products from FakeStore API and populate Weaviate database.
No authentication required - completely free!
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from db import WeaviateConnection
from services import get_clip_service
from typing import List, Dict, Any

class FakeStoreProductFetcher:
    """Fetch products from FakeStore API and insert into Weaviate."""
    
    BASE_URL = "https://fakestoreapi.com"
    
    def __init__(self):
        self.clip_service = get_clip_service()
    
    def fetch_all_products(self) -> List[Dict[str, Any]]:
        """
        Fetch all products from FakeStore API.
        
        Returns:
            List of product dictionaries
        """
        try:
            print("Fetching products from FakeStore API...")
            response = requests.get(f"{self.BASE_URL}/products")
            response.raise_for_status()
            products = response.json()
            print(f"✓ Successfully fetched {len(products)} products")
            return products
        except Exception as e:
            print(f"✗ Failed to fetch products: {e}")
            raise
    
    def fetch_categories(self) -> List[str]:
        """Get all available categories."""
        try:
            response = requests.get(f"{self.BASE_URL}/products/categories")
            response.raise_for_status()
            categories = response.json()
            return categories
        except Exception as e:
            print(f"✗ Failed to fetch categories: {e}")
            return []
    
    def extract_color_from_title(self, title: str) -> str:
        """
        Try to extract color from product title.
        
        Args:
            title: Product title
            
        Returns:
            Color string or "multicolor"
        """
        colors = {
            'red': ['red'],
            'blue': ['blue'],
            'black': ['black'],
            'white': ['white'],
            'green': ['green'],
            'yellow': ['yellow'],
            'purple': ['purple'],
            'pink': ['pink'],
            'brown': ['brown', 'beige', 'tan'],
            'gray': ['gray', 'grey', 'silver'],
            'gold': ['gold', 'golden'],
        }
        
        title_lower = title.lower()
        for color, keywords in colors.items():
            for keyword in keywords:
                if keyword in title_lower:
                    return color
        
        return "multicolor"
    
    def transform_products(self, raw_products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform FakeStore products to our schema.
        
        Args:
            raw_products: Products from FakeStore API
            
        Returns:
            Transformed products ready for Weaviate
        """
        transformed = []
        
        for i, product in enumerate(raw_products):
            # Extract color from title
            color = self.extract_color_from_title(product.get("title", ""))
            
            transformed_product = {
                "product_id": f"fakestore_{product['id']}",
                "title": product.get("title", ""),
                "description": product.get("description", ""),
                "color": color,
                "category": product.get("category", "other"),
                "image_path": product.get("image", f"/images/product-{i}.jpg"),
                "price": product.get("price", 0),
                "rating": product.get("rating", {}).get("rate", 0) if product.get("rating") else 0
            }
            transformed.append(transformed_product)
        
        return transformed
    
    def populate_weaviate(self, limit: int = None):
        """
        Fetch products and populate Weaviate.
        
        Args:
            limit: Maximum number of products to add (None = all)
        """
        # Fetch products
        raw_products = self.fetch_all_products()
        
        if limit:
            raw_products = raw_products[:limit]
        
        # Transform products
        print(f"\nTransforming {len(raw_products)} products...")
        products = self.transform_products(raw_products)
        
        # Connect to Weaviate
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
            print(f"\nAdding {len(products)} products to Weaviate...")
            for i, product in enumerate(products, 1):
                try:
                    # Generate embedding from title and description
                    text_to_embed = f"{product['title']}. {product['description']}"
                    embedding = self.clip_service.embed_text(text_to_embed)
                    
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
                    
                    if i % 5 == 0:
                        print(f"  ✓ {i}/{len(products)}: {product['title'][:50]}...")
                    
                except Exception as e:
                    print(f"  ✗ Failed to add product {product['title']}: {e}")
            
            # Verify
            info = client.get_collection_info()
            print(f"\n✓ Successfully added {info['total_objects']} products from FakeStore API!")
            print(f"\nNow you can search for products in any category:")
            print(f"  - electronics")
            print(f"  - jewelery")
            print(f"  - men's clothing")
            print(f"  - women's clothing")

def main():
    """Main entry point."""
    fetcher = FakeStoreProductFetcher()
    
    # Fetch and populate - limit to 20 for faster demo (remove limit for all)
    fetcher.populate_weaviate(limit=20)

if __name__ == "__main__":
    main()
