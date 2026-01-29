from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class Product(BaseModel):
    """Product schema for MongoDB storage."""
    
    product_id: str = Field(..., description="Unique product identifier")
    title: str = Field(..., description="Product title")
    description: str = Field(..., description="Product description")
    image_path: str = Field(..., description="Path to product image")
    color: str = Field(..., description="Product color")
    category: str = Field(..., description="Product category")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "product_id": "PROD-001",
                "title": "Blue Cotton T-Shirt",
                "description": "Comfortable cotton t-shirt in blue",
                "image_path": "/images/products/tshirt-001.jpg",
                "color": "blue",
                "category": "apparel"
            }
        }


class ProductInDB(Product):
    """Product schema with MongoDB _id field."""
    
    id: Optional[str] = Field(default=None, alias="_id")
    
    class Config:
        populate_by_name = True
