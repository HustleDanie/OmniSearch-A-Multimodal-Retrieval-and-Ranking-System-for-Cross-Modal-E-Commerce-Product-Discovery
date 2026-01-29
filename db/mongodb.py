from pymongo import MongoClient, ASCENDING
from pymongo.collection import Collection
from pymongo.database import Database
from typing import List, Optional, Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()


class MongoDBClient:
    """MongoDB client for managing product data."""
    
    def __init__(self, uri: Optional[str] = None, db_name: str = "omnisearch"):
        """
        Initialize MongoDB client.
        
        Args:
            uri: MongoDB connection URI. If None, uses MONGO_URI from environment.
            db_name: Name of the database to use.
        """
        self.uri = uri or os.getenv("MONGO_URI", "mongodb://localhost:27017")
        self.db_name = db_name
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None
        self.products: Optional[Collection] = None
        
    def connect(self) -> None:
        """Establish connection to MongoDB."""
        try:
            self.client = MongoClient(self.uri)
            self.db = self.client[self.db_name]
            self.products = self.db["products"]
            
            # Create indexes for efficient querying
            self.products.create_index([("product_id", ASCENDING)], unique=True)
            self.products.create_index([("category", ASCENDING)])
            self.products.create_index([("color", ASCENDING)])
            
            # Test connection
            self.client.admin.command('ping')
            print(f"✓ Connected to MongoDB: {self.db_name}")
            
        except Exception as e:
            print(f"✗ Failed to connect to MongoDB: {e}")
            raise
    
    def disconnect(self) -> None:
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            print("✓ Disconnected from MongoDB")
    
    def insert_product(self, product: Dict[str, Any]) -> str:
        """
        Insert a single product into the database.
        
        Args:
            product: Dictionary containing product data.
            
        Returns:
            The inserted document's ID as a string.
            
        Raises:
            ValueError: If product_id already exists.
        """
        if not self.products:
            raise RuntimeError("Not connected to MongoDB. Call connect() first.")
        
        try:
            result = self.products.insert_one(product)
            print(f"✓ Inserted product: {product.get('product_id')}")
            return str(result.inserted_id)
        except Exception as e:
            print(f"✗ Failed to insert product: {e}")
            raise
    
    def insert_products(self, products: List[Dict[str, Any]]) -> List[str]:
        """
        Insert multiple products into the database.
        
        Args:
            products: List of dictionaries containing product data.
            
        Returns:
            List of inserted document IDs as strings.
        """
        if not self.products:
            raise RuntimeError("Not connected to MongoDB. Call connect() first.")
        
        try:
            result = self.products.insert_many(products, ordered=False)
            print(f"✓ Inserted {len(result.inserted_ids)} products")
            return [str(id) for id in result.inserted_ids]
        except Exception as e:
            print(f"✗ Failed to insert products: {e}")
            raise
    
    def fetch_all_products(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fetch all products from the database.
        
        Args:
            limit: Maximum number of products to return. None returns all.
            
        Returns:
            List of product dictionaries.
        """
        if not self.products:
            raise RuntimeError("Not connected to MongoDB. Call connect() first.")
        
        try:
            cursor = self.products.find()
            
            if limit:
                cursor = cursor.limit(limit)
            
            products = list(cursor)
            
            # Convert ObjectId to string for JSON serialization
            for product in products:
                if "_id" in product:
                    product["_id"] = str(product["_id"])
            
            print(f"✓ Fetched {len(products)} products")
            return products
            
        except Exception as e:
            print(f"✗ Failed to fetch products: {e}")
            raise
    
    def fetch_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a single product by product_id.
        
        Args:
            product_id: The unique product identifier.
            
        Returns:
            Product dictionary or None if not found.
        """
        if not self.products:
            raise RuntimeError("Not connected to MongoDB. Call connect() first.")
        
        try:
            product = self.products.find_one({"product_id": product_id})
            
            if product and "_id" in product:
                product["_id"] = str(product["_id"])
            
            return product
            
        except Exception as e:
            print(f"✗ Failed to fetch product: {e}")
            raise
    
    def fetch_products_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        Fetch all products in a specific category.
        
        Args:
            category: The category to filter by.
            
        Returns:
            List of product dictionaries.
        """
        if not self.products:
            raise RuntimeError("Not connected to MongoDB. Call connect() first.")
        
        try:
            products = list(self.products.find({"category": category}))
            
            for product in products:
                if "_id" in product:
                    product["_id"] = str(product["_id"])
            
            print(f"✓ Fetched {len(products)} products in category '{category}'")
            return products
            
        except Exception as e:
            print(f"✗ Failed to fetch products by category: {e}")
            raise
    
    def delete_all_products(self) -> int:
        """
        Delete all products from the database.
        
        Returns:
            Number of documents deleted.
        """
        if not self.products:
            raise RuntimeError("Not connected to MongoDB. Call connect() first.")
        
        try:
            result = self.products.delete_many({})
            print(f"✓ Deleted {result.deleted_count} products")
            return result.deleted_count
            
        except Exception as e:
            print(f"✗ Failed to delete products: {e}")
            raise


# Context manager support
class MongoDBConnection:
    """Context manager for MongoDB connections."""
    
    def __init__(self, uri: Optional[str] = None, db_name: str = "omnisearch"):
        self.client = MongoDBClient(uri, db_name)
    
    def __enter__(self) -> MongoDBClient:
        self.client.connect()
        return self.client
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.disconnect()
        return False
