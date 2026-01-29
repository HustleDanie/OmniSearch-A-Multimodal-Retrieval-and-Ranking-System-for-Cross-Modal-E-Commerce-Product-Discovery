from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class UserProfile(BaseModel):
    """User profile schema for MongoDB storage."""
    
    user_id: str = Field(..., description="Unique user identifier")
    past_purchases: List[str] = Field(default_factory=list, description="List of purchased product titles")
    preferred_colors: List[str] = Field(default_factory=list, description="Preferred product colors")
    preferred_categories: List[str] = Field(default_factory=list, description="Preferred product categories")
    price_range: dict = Field(
        default_factory=lambda: {"min": 0, "max": 1000},
        description="Price range with min and max values"
    )
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "USER-001",
                "past_purchases": ["Blue Running Shoes", "Cotton T-Shirt", "Summer Dress"],
                "preferred_colors": ["blue", "black", "gray"],
                "preferred_categories": ["footwear", "apparel"],
                "price_range": {"min": 20, "max": 200}
            }
        }


class UserProfileInDB(UserProfile):
    """User profile schema with MongoDB _id field."""
    
    id: Optional[str] = Field(default=None, alias="_id")
    
    class Config:
        populate_by_name = True


class UserPreferences(BaseModel):
    """Schema for updating user preferences."""
    
    preferred_colors: Optional[List[str]] = None
    preferred_categories: Optional[List[str]] = None
    price_range: Optional[dict] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "preferred_colors": ["red", "green"],
                "preferred_categories": ["shoes", "bags"],
                "price_range": {"min": 50, "max": 300}
            }
        }
