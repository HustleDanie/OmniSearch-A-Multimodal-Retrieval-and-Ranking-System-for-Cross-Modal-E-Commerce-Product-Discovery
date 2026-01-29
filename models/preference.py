from pydantic import BaseModel, Field
from typing import Dict, List, Optional


class PreferenceAnalysis(BaseModel):
    """Result of analyzing user preferences from purchase history."""
    
    dominant_colors: Dict[str, int] = Field(
        default_factory=dict,
        description="Colors extracted from titles with frequency count"
    )
    most_frequent_categories: Dict[str, int] = Field(
        default_factory=dict,
        description="Categories with frequency count"
    )
    style_keywords: Dict[str, int] = Field(
        default_factory=dict,
        description="Style-related keywords with frequency count"
    )
    product_types: Dict[str, int] = Field(
        default_factory=dict,
        description="Product types extracted from titles with frequency"
    )
    purchase_count: int = Field(
        default=0,
        description="Total number of purchases analyzed"
    )
    unique_colors: int = Field(
        default=0,
        description="Total unique colors found"
    )
    unique_categories: int = Field(
        default=0,
        description="Total unique categories"
    )
    unique_keywords: int = Field(
        default=0,
        description="Total unique style keywords found"
    )
    inferred_style: str = Field(
        default="Unknown",
        description="Inferred style profile based on keywords"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "dominant_colors": {"blue": 4, "black": 3, "white": 2},
                "most_frequent_categories": {"apparel": 5, "footwear": 3},
                "style_keywords": {"casual": 3, "comfortable": 2, "classic": 1},
                "product_types": {"shirt": 3, "shoe": 2, "dress": 1},
                "purchase_count": 9,
                "unique_colors": 5,
                "unique_categories": 2,
                "unique_keywords": 4,
                "inferred_style": "Casual, Comfortable, Classic"
            }
        }


class PreferenceInsights(BaseModel):
    """Simplified insights from preference analysis."""
    
    user_id: Optional[str] = None
    top_colors: List[str] = Field(
        default_factory=list,
        description="Top 3 dominant colors"
    )
    top_categories: List[str] = Field(
        default_factory=list,
        description="Top 3 most frequent categories"
    )
    top_style_keywords: List[str] = Field(
        default_factory=list,
        description="Top 5 style keywords"
    )
    style_profile: str = Field(
        default="Unknown",
        description="Inferred style profile"
    )
    analysis_summary: str = Field(
        default="",
        description="Human-readable summary of preferences"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "USER-001",
                "top_colors": ["blue", "black", "white"],
                "top_categories": ["apparel", "footwear"],
                "top_style_keywords": ["casual", "comfortable", "classic"],
                "style_profile": "Casual, Comfortable, Classic",
                "analysis_summary": "User prefers casual, comfortable styles in blue and black"
            }
        }
