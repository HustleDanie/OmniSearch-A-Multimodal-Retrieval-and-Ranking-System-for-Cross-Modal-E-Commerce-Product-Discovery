"""
MongoDB service for managing user profiles.
"""
from pymongo import MongoClient, ASCENDING
from pymongo.collection import Collection
from pymongo.database import Database
from typing import List, Optional, Dict, Any
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()


class UserProfileService:
    """MongoDB service for managing user profiles."""
    
    def __init__(self, uri: Optional[str] = None, db_name: str = "omnisearch"):
        """
        Initialize UserProfileService.
        
        Args:
            uri: MongoDB connection URI. If None, uses MONGO_URI from environment.
            db_name: Name of the database to use.
        """
        self.uri = uri or os.getenv("MONGO_URI", "mongodb://localhost:27017")
        self.db_name = db_name
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None
        self.users: Optional[Collection] = None
    
    def connect(self) -> None:
        """Establish connection to MongoDB."""
        try:
            self.client = MongoClient(self.uri)
            self.db = self.client[self.db_name]
            self.users = self.db["users"]
            
            # Create indexes for efficient querying
            self.users.create_index([("user_id", ASCENDING)], unique=True)
            self.users.create_index([("created_at", ASCENDING)])
            
            # Test connection
            self.client.admin.command('ping')
            print(f"✓ Connected to MongoDB: {self.db_name} (users collection)")
            
        except Exception as e:
            print(f"✗ Failed to connect to MongoDB: {e}")
            raise
    
    def disconnect(self) -> None:
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            print("✓ Disconnected from MongoDB (users collection)")
    
    def create_user_profile(
        self,
        user_id: str,
        past_purchases: Optional[List[str]] = None,
        preferred_colors: Optional[List[str]] = None,
        preferred_categories: Optional[List[str]] = None,
        price_range: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Create a new user profile.
        
        Args:
            user_id: Unique user identifier.
            past_purchases: List of purchased product titles.
            preferred_colors: List of preferred colors.
            preferred_categories: List of preferred categories.
            price_range: Dictionary with 'min' and 'max' price limits.
            
        Returns:
            The created user profile document.
            
        Raises:
            ValueError: If user_id already exists.
            RuntimeError: If not connected to MongoDB.
        """
        if not self.users:
            raise RuntimeError("Not connected to MongoDB. Call connect() first.")
        
        try:
            # Check if user already exists
            existing = self.users.find_one({"user_id": user_id})
            if existing:
                raise ValueError(f"User profile with user_id '{user_id}' already exists")
            
            now = datetime.utcnow()
            user_profile = {
                "user_id": user_id,
                "past_purchases": past_purchases or [],
                "preferred_colors": preferred_colors or [],
                "preferred_categories": preferred_categories or [],
                "price_range": price_range or {"min": 0, "max": 1000},
                "created_at": now,
                "updated_at": now
            }
            
            result = self.users.insert_one(user_profile)
            user_profile["_id"] = str(result.inserted_id)
            
            print(f"✓ Created user profile: {user_id}")
            return user_profile
            
        except ValueError:
            raise
        except Exception as e:
            print(f"✗ Failed to create user profile: {e}")
            raise
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a user profile by user_id.
        
        Args:
            user_id: Unique user identifier.
            
        Returns:
            User profile dictionary or None if not found.
            
        Raises:
            RuntimeError: If not connected to MongoDB.
        """
        if not self.users:
            raise RuntimeError("Not connected to MongoDB. Call connect() first.")
        
        try:
            user = self.users.find_one({"user_id": user_id})
            
            if user and "_id" in user:
                user["_id"] = str(user["_id"])
            
            if user:
                print(f"✓ Retrieved user profile: {user_id}")
            else:
                print(f"⚠ User profile not found: {user_id}")
            
            return user
            
        except Exception as e:
            print(f"✗ Failed to retrieve user profile: {e}")
            raise
    
    def update_preferences(
        self,
        user_id: str,
        preferred_colors: Optional[List[str]] = None,
        preferred_categories: Optional[List[str]] = None,
        price_range: Optional[Dict[str, float]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update user preferences (colors, categories, price range).
        
        Args:
            user_id: Unique user identifier.
            preferred_colors: New list of preferred colors (replaces existing).
            preferred_categories: New list of preferred categories (replaces existing).
            price_range: New price range dictionary with 'min' and 'max'.
            
        Returns:
            Updated user profile dictionary or None if user not found.
            
        Raises:
            RuntimeError: If not connected to MongoDB.
        """
        if not self.users:
            raise RuntimeError("Not connected to MongoDB. Call connect() first.")
        
        try:
            # Build update dict with only provided fields
            update_fields = {"updated_at": datetime.utcnow()}
            
            if preferred_colors is not None:
                update_fields["preferred_colors"] = preferred_colors
            if preferred_categories is not None:
                update_fields["preferred_categories"] = preferred_categories
            if price_range is not None:
                update_fields["price_range"] = price_range
            
            result = self.users.find_one_and_update(
                {"user_id": user_id},
                {"$set": update_fields},
                return_document=True
            )
            
            if result:
                if "_id" in result:
                    result["_id"] = str(result["_id"])
                print(f"✓ Updated preferences for user: {user_id}")
                return result
            else:
                print(f"⚠ User not found: {user_id}")
                return None
                
        except Exception as e:
            print(f"✗ Failed to update user preferences: {e}")
            raise
    
    def add_purchase(self, user_id: str, product_title: str) -> Optional[Dict[str, Any]]:
        """
        Add a product title to user's past purchases.
        
        Args:
            user_id: Unique user identifier.
            product_title: Title of purchased product.
            
        Returns:
            Updated user profile or None if user not found.
            
        Raises:
            RuntimeError: If not connected to MongoDB.
        """
        if not self.users:
            raise RuntimeError("Not connected to MongoDB. Call connect() first.")
        
        try:
            result = self.users.find_one_and_update(
                {"user_id": user_id},
                {
                    "$addToSet": {"past_purchases": product_title},
                    "$set": {"updated_at": datetime.utcnow()}
                },
                return_document=True
            )
            
            if result:
                if "_id" in result:
                    result["_id"] = str(result["_id"])
                print(f"✓ Added purchase to user profile: {user_id}")
                return result
            else:
                print(f"⚠ User not found: {user_id}")
                return None
                
        except Exception as e:
            print(f"✗ Failed to add purchase: {e}")
            raise
    
    def update_user_memory(
        self, 
        user_id: str, 
        product: Dict[str, Any],
        auto_update_preferences: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Update user memory after a recommendation is clicked or purchased.
        Appends product to purchase history and optionally updates preferences.
        
        Args:
            user_id: Unique user identifier.
            product: Product dictionary with fields: title, color, category, price, etc.
            auto_update_preferences: If True, automatically update user preferences based on the product.
            
        Returns:
            Updated user profile or None if user not found.
            
        Raises:
            RuntimeError: If not connected to MongoDB.
            ValueError: If product missing required fields.
            
        Example:
            >>> product = {
            ...     "title": "Blue Casual Shirt",
            ...     "color": "blue",
            ...     "category": "apparel",
            ...     "price": 49.99
            ... }
            >>> service.update_user_memory("user123", product)
        """
        if not self.users:
            raise RuntimeError("Not connected to MongoDB. Call connect() first.")
        
        # Validate product has required fields
        product_title = product.get("title")
        if not product_title:
            raise ValueError("Product must have 'title' field")
        
        try:
            # Get current user profile
            user_profile = self.get_user_profile(user_id)
            
            if not user_profile:
                print(f"⚠ User not found: {user_id}. Creating new profile.")
                # Create new profile if user doesn't exist
                user_profile = self.create_user_profile(user_id)
            
            # Build update operations
            update_ops = {
                "$addToSet": {"past_purchases": product_title},
                "$set": {"updated_at": datetime.utcnow()}
            }
            
            # Optionally update preferences based on the product
            if auto_update_preferences:
                preference_updates = {}
                
                # Add color preference
                product_color = product.get("color")
                if product_color and product_color.strip():
                    color_lower = product_color.lower()
                    current_colors = user_profile.get("preferred_colors", [])
                    if color_lower not in [c.lower() for c in current_colors]:
                        update_ops["$addToSet"]["preferred_colors"] = color_lower
                
                # Add category preference
                product_category = product.get("category")
                if product_category and product_category.strip():
                    category_lower = product_category.lower()
                    current_categories = user_profile.get("preferred_categories", [])
                    if category_lower not in [c.lower() for c in current_categories]:
                        update_ops["$addToSet"]["preferred_categories"] = category_lower
                
                # Update price range if product is outside current range
                product_price = product.get("price")
                if product_price is not None:
                    current_price_range = user_profile.get("price_range", {"min": 0, "max": 1000})
                    new_min = min(current_price_range.get("min", 0), product_price)
                    new_max = max(current_price_range.get("max", 1000), product_price)
                    
                    # Only update if changed
                    if new_min != current_price_range.get("min") or new_max != current_price_range.get("max"):
                        update_ops["$set"]["price_range"] = {"min": new_min, "max": new_max}
            
            # Perform the update
            result = self.users.find_one_and_update(
                {"user_id": user_id},
                update_ops,
                return_document=True
            )
            
            if result:
                if "_id" in result:
                    result["_id"] = str(result["_id"])
                print(f"✓ Updated user memory for: {user_id}")
                print(f"  - Added purchase: {product_title}")
                if auto_update_preferences:
                    print(f"  - Updated preferences from product attributes")
                return result
            else:
                print(f"⚠ Failed to update user: {user_id}")
                return None
                
        except ValueError:
            raise
        except Exception as e:
            print(f"✗ Failed to update user memory: {e}")
            raise
    
    def get_all_users(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fetch all user profiles from the database.
        
        Args:
            limit: Maximum number of users to return. None returns all.
            
        Returns:
            List of user profile dictionaries.
            
        Raises:
            RuntimeError: If not connected to MongoDB.
        """
        if not self.users:
            raise RuntimeError("Not connected to MongoDB. Call connect() first.")
        
        try:
            cursor = self.users.find()
            
            if limit:
                cursor = cursor.limit(limit)
            
            users = list(cursor)
            
            # Convert ObjectId to string for JSON serialization
            for user in users:
                if "_id" in user:
                    user["_id"] = str(user["_id"])
            
            print(f"✓ Fetched {len(users)} user profiles")
            return users
            
        except Exception as e:
            print(f"✗ Failed to fetch user profiles: {e}")
            raise
    
    def delete_user_profile(self, user_id: str) -> bool:
        """
        Delete a user profile by user_id.
        
        Args:
            user_id: Unique user identifier.
            
        Returns:
            True if user was deleted, False if not found.
            
        Raises:
            RuntimeError: If not connected to MongoDB.
        """
        if not self.users:
            raise RuntimeError("Not connected to MongoDB. Call connect() first.")
        
        try:
            result = self.users.delete_one({"user_id": user_id})
            
            if result.deleted_count > 0:
                print(f"✓ Deleted user profile: {user_id}")
                return True
            else:
                print(f"⚠ User profile not found: {user_id}")
                return False
                
        except Exception as e:
            print(f"✗ Failed to delete user profile: {e}")
            raise
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
