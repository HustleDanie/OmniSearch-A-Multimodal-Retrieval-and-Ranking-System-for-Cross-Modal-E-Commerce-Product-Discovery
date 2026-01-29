"""
Unit tests for user profile models and service logic.
Tests validation and schema without requiring MongoDB.
"""
import pytest
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.user import UserProfile, UserProfileInDB, UserPreferences


class TestUserProfileModel:
    """Test UserProfile Pydantic model."""
    
    def test_create_basic_profile(self):
        """Test creating a basic user profile."""
        profile = UserProfile(
            user_id="USER-001",
            past_purchases=["Blue Shoes"],
            preferred_colors=["blue", "black"],
            preferred_categories=["footwear"],
            price_range={"min": 20, "max": 150}
        )
        
        assert profile.user_id == "USER-001"
        assert "Blue Shoes" in profile.past_purchases
        assert "blue" in profile.preferred_colors
        assert profile.price_range["min"] == 20
    
    def test_profile_with_defaults(self):
        """Test that fields have appropriate defaults."""
        profile = UserProfile(user_id="USER-002")
        
        assert profile.user_id == "USER-002"
        assert profile.past_purchases == []
        assert profile.preferred_colors == []
        assert profile.preferred_categories == []
        assert profile.price_range == {"min": 0, "max": 1000}
        assert profile.created_at is not None
        assert profile.updated_at is not None
    
    def test_profile_json_serialization(self):
        """Test JSON serialization of user profile."""
        profile = UserProfile(
            user_id="USER-003",
            past_purchases=["Item1", "Item2"],
            preferred_colors=["red"],
            preferred_categories=["apparel"]
        )
        
        json_data = profile.model_dump()
        assert json_data["user_id"] == "USER-003"
        assert len(json_data["past_purchases"]) == 2
        assert "created_at" in json_data
    
    def test_profile_with_multiple_preferences(self):
        """Test profile with multiple preferences."""
        profile = UserProfile(
            user_id="USER-004",
            past_purchases=[
                "Red Dress",
                "Black Shoes",
                "White T-Shirt",
                "Blue Jeans"
            ],
            preferred_colors=["red", "black", "white", "blue"],
            preferred_categories=["apparel", "footwear", "accessories"],
            price_range={"min": 30, "max": 250}
        )
        
        assert len(profile.past_purchases) == 4
        assert len(profile.preferred_colors) == 4
        assert len(profile.preferred_categories) == 3
        assert profile.price_range["max"] == 250
    
    def test_price_range_validation(self):
        """Test price range is properly stored."""
        price_ranges = [
            {"min": 0, "max": 50},
            {"min": 100, "max": 500},
            {"min": 50, "max": 200}
        ]
        
        for pr in price_ranges:
            profile = UserProfile(user_id="TEST", price_range=pr)
            assert profile.price_range == pr


class TestUserPreferencesModel:
    """Test UserPreferences Pydantic model for updates."""
    
    def test_partial_update_colors(self):
        """Test updating only colors."""
        prefs = UserPreferences(
            preferred_colors=["green", "yellow"]
        )
        
        assert prefs.preferred_colors == ["green", "yellow"]
        assert prefs.preferred_categories is None
        assert prefs.price_range is None
    
    def test_partial_update_categories(self):
        """Test updating only categories."""
        prefs = UserPreferences(
            preferred_categories=["shoes", "bags"]
        )
        
        assert prefs.preferred_colors is None
        assert prefs.preferred_categories == ["shoes", "bags"]
        assert prefs.price_range is None
    
    def test_partial_update_price(self):
        """Test updating only price range."""
        prefs = UserPreferences(
            price_range={"min": 50, "max": 300}
        )
        
        assert prefs.preferred_colors is None
        assert prefs.preferred_categories is None
        assert prefs.price_range == {"min": 50, "max": 300}
    
    def test_full_preferences_update(self):
        """Test updating all preferences at once."""
        prefs = UserPreferences(
            preferred_colors=["red", "pink"],
            preferred_categories=["apparel", "accessories"],
            price_range={"min": 25, "max": 150}
        )
        
        assert prefs.preferred_colors == ["red", "pink"]
        assert prefs.preferred_categories == ["apparel", "accessories"]
        assert prefs.price_range["min"] == 25


class TestUserProfileInDB:
    """Test UserProfileInDB with MongoDB _id field."""
    
    def test_profile_in_db_with_id(self):
        """Test UserProfileInDB with _id field."""
        profile = UserProfileInDB(
            _id="507f1f77bcf86cd799439011",
            user_id="USER-005",
            past_purchases=["Item1"],
            preferred_colors=["blue"]
        )
        
        assert profile.id == "507f1f77bcf86cd799439011"
        assert profile.user_id == "USER-005"
    
    def test_profile_in_db_without_id(self):
        """Test UserProfileInDB can be created without _id."""
        profile = UserProfileInDB(
            user_id="USER-006",
            past_purchases=[]
        )
        
        assert profile.id is None
        assert profile.user_id == "USER-006"


class TestUserProfileValidation:
    """Test validation and edge cases."""
    
    def test_empty_lists_are_valid(self):
        """Empty lists should be valid."""
        profile = UserProfile(
            user_id="TEST-EMPTY",
            past_purchases=[],
            preferred_colors=[],
            preferred_categories=[]
        )
        
        assert profile.past_purchases == []
        assert profile.preferred_colors == []
    
    def test_user_id_required(self):
        """Test that user_id is required."""
        with pytest.raises(Exception):
            UserProfile()
    
    def test_duplicate_preferences_allowed(self):
        """Test that duplicate colors/categories are allowed."""
        profile = UserProfile(
            user_id="TEST-DUP",
            preferred_colors=["blue", "blue", "blue"],
            past_purchases=["Item1", "Item1"]
        )
        
        assert profile.preferred_colors.count("blue") == 3
        assert profile.past_purchases.count("Item1") == 2
    
    def test_large_purchase_history(self):
        """Test handling large purchase history."""
        purchases = [f"Product-{i}" for i in range(1000)]
        profile = UserProfile(
            user_id="TEST-LARGE",
            past_purchases=purchases
        )
        
        assert len(profile.past_purchases) == 1000
    
    def test_special_characters_in_text(self):
        """Test special characters in user data."""
        profile = UserProfile(
            user_id="USER-SPECIAL-123",
            past_purchases=["Blue T-Shirt (Large)", "Red Shoes - Nike"],
            preferred_colors=["blue/green", "red-pink"],
            preferred_categories=["apparel & shoes"]
        )
        
        assert "Blue T-Shirt (Large)" in profile.past_purchases
        assert "blue/green" in profile.preferred_colors


class TestUserProfileComparison:
    """Test profile comparison and operations."""
    
    def test_profile_equality_same_data(self):
        """Test profiles with same data are equal."""
        data = {
            "user_id": "USER-EQ",
            "past_purchases": ["Item1"],
            "preferred_colors": ["blue"],
            "preferred_categories": ["shoes"],
            "price_range": {"min": 10, "max": 100}
        }
        
        profile1 = UserProfile(**data)
        profile2 = UserProfile(**data)
        
        # Both should have same user_id and preferences
        assert profile1.user_id == profile2.user_id
        assert profile1.preferred_colors == profile2.preferred_colors
    
    def test_profile_field_access(self):
        """Test accessing profile fields."""
        profile = UserProfile(
            user_id="USER-ACCESS",
            past_purchases=["Shoes", "Hat"],
            preferred_colors=["black"],
            preferred_categories=["accessories"],
            price_range={"min": 5, "max": 50}
        )
        
        # Access individual fields
        assert profile.user_id == "USER-ACCESS"
        assert profile.past_purchases[0] == "Shoes"
        assert profile.preferred_colors[0] == "black"
        assert profile.preferred_categories[0] == "accessories"
        assert profile.price_range["min"] == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
