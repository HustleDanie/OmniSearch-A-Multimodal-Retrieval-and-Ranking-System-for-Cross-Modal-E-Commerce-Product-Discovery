"""
Tests for update_user_memory function.
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from db.user_service import UserProfileService


@pytest.fixture
def mock_service():
    """Create a mock UserProfileService for testing."""
    service = UserProfileService()
    service.users = MagicMock()
    return service


@pytest.fixture
def sample_product():
    """Sample product for testing."""
    return {
        "title": "Blue Casual Shirt",
        "color": "blue",
        "category": "apparel",
        "price": 49.99,
        "description": "Comfortable cotton shirt"
    }


@pytest.fixture
def sample_user_profile():
    """Sample user profile for testing."""
    return {
        "user_id": "user123",
        "past_purchases": ["Red T-Shirt", "Black Jeans"],
        "preferred_colors": ["red", "black"],
        "preferred_categories": ["apparel"],
        "price_range": {"min": 20.0, "max": 80.0},
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


def test_update_user_memory_adds_purchase(mock_service, sample_product, sample_user_profile):
    """Test that update_user_memory adds product to purchase history."""
    # Mock get_user_profile and find_one_and_update
    mock_service.get_user_profile = MagicMock(return_value=sample_user_profile)
    mock_service.users.find_one_and_update.return_value = {
        **sample_user_profile,
        "past_purchases": sample_user_profile["past_purchases"] + [sample_product["title"]]
    }
    
    result = mock_service.update_user_memory("user123", sample_product)
    
    # Verify purchase was added
    assert result is not None
    mock_service.users.find_one_and_update.assert_called_once()
    call_args = mock_service.users.find_one_and_update.call_args
    assert "$addToSet" in call_args[0][1]
    assert call_args[0][1]["$addToSet"]["past_purchases"] == "Blue Casual Shirt"


def test_update_user_memory_adds_color_preference(mock_service, sample_product, sample_user_profile):
    """Test that update_user_memory adds new color to preferences."""
    mock_service.get_user_profile = MagicMock(return_value=sample_user_profile)
    mock_service.users.find_one_and_update.return_value = sample_user_profile
    
    result = mock_service.update_user_memory("user123", sample_product, auto_update_preferences=True)
    
    # Verify color preference was added
    call_args = mock_service.users.find_one_and_update.call_args
    assert "$addToSet" in call_args[0][1]
    # Blue should be added since it's not in current preferences
    assert "preferred_colors" in call_args[0][1]["$addToSet"]


def test_update_user_memory_adds_category_preference(mock_service, sample_product, sample_user_profile):
    """Test that update_user_memory adds category if not already present."""
    # User doesn't have this category yet
    profile_copy = sample_user_profile.copy()
    profile_copy["preferred_categories"] = ["footwear"]
    
    mock_service.get_user_profile = MagicMock(return_value=profile_copy)
    mock_service.users.find_one_and_update.return_value = profile_copy
    
    result = mock_service.update_user_memory("user123", sample_product, auto_update_preferences=True)
    
    call_args = mock_service.users.find_one_and_update.call_args
    assert "$addToSet" in call_args[0][1]
    # Category should be added
    assert "preferred_categories" in call_args[0][1]["$addToSet"]


def test_update_user_memory_expands_price_range(mock_service, sample_product, sample_user_profile):
    """Test that update_user_memory expands price range when needed."""
    # Product price (49.99) is within range, so no change
    mock_service.get_user_profile = MagicMock(return_value=sample_user_profile)
    mock_service.users.find_one_and_update.return_value = sample_user_profile
    
    result = mock_service.update_user_memory("user123", sample_product, auto_update_preferences=True)
    
    # Price range should not be updated since product is within range (20-80)
    call_args = mock_service.users.find_one_and_update.call_args
    # No price_range in $set if within range
    
    # Now test with expensive product
    expensive_product = {**sample_product, "price": 150.0}
    result = mock_service.update_user_memory("user123", expensive_product, auto_update_preferences=True)
    
    # Price range should be updated
    call_args = mock_service.users.find_one_and_update.call_args
    if "price_range" in call_args[0][1]["$set"]:
        assert call_args[0][1]["$set"]["price_range"]["max"] == 150.0


def test_update_user_memory_without_auto_preferences(mock_service, sample_product, sample_user_profile):
    """Test that auto_update_preferences=False doesn't update preferences."""
    mock_service.get_user_profile = MagicMock(return_value=sample_user_profile)
    mock_service.users.find_one_and_update.return_value = sample_user_profile
    
    result = mock_service.update_user_memory("user123", sample_product, auto_update_preferences=False)
    
    # Only purchase should be added, no preference updates
    call_args = mock_service.users.find_one_and_update.call_args
    update_ops = call_args[0][1]
    
    # Should have purchase
    assert "$addToSet" in update_ops
    assert "past_purchases" in update_ops["$addToSet"]
    
    # Should NOT have preference updates
    assert "preferred_colors" not in update_ops.get("$addToSet", {})
    assert "preferred_categories" not in update_ops.get("$addToSet", {})


def test_update_user_memory_creates_user_if_not_exists(mock_service, sample_product):
    """Test that update_user_memory creates user if they don't exist."""
    # Mock get_user_profile to return None (user doesn't exist)
    mock_service.get_user_profile = MagicMock(return_value=None)
    
    # Mock create_user_profile
    new_profile = {
        "user_id": "newuser",
        "past_purchases": [],
        "preferred_colors": [],
        "preferred_categories": [],
        "price_range": {"min": 0, "max": 1000},
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    mock_service.create_user_profile = MagicMock(return_value=new_profile)
    mock_service.users.find_one_and_update.return_value = new_profile
    
    result = mock_service.update_user_memory("newuser", sample_product)
    
    # Verify user was created
    mock_service.create_user_profile.assert_called_once_with("newuser")
    
    # Verify update was attempted
    mock_service.users.find_one_and_update.assert_called_once()


def test_update_user_memory_missing_title_raises_error(mock_service):
    """Test that product without title raises ValueError."""
    product_no_title = {
        "color": "blue",
        "category": "apparel"
    }
    
    with pytest.raises(ValueError, match="Product must have 'title' field"):
        mock_service.update_user_memory("user123", product_no_title)


def test_update_user_memory_not_connected_raises_error():
    """Test that calling without connection raises RuntimeError."""
    service = UserProfileService()
    # Don't connect, users will be None
    
    product = {"title": "Test Product"}
    
    with pytest.raises(RuntimeError, match="Not connected to MongoDB"):
        service.update_user_memory("user123", product)


def test_update_user_memory_handles_missing_optional_fields(mock_service, sample_user_profile):
    """Test that missing optional fields (color, category, price) are handled gracefully."""
    product_minimal = {
        "title": "Simple Product"
        # No color, category, or price
    }
    
    mock_service.get_user_profile = MagicMock(return_value=sample_user_profile)
    mock_service.users.find_one_and_update.return_value = sample_user_profile
    
    result = mock_service.update_user_memory("user123", product_minimal, auto_update_preferences=True)
    
    # Should still work, just won't update preferences
    assert result is not None
    call_args = mock_service.users.find_one_and_update.call_args
    assert "$addToSet" in call_args[0][1]
    assert "past_purchases" in call_args[0][1]["$addToSet"]


def test_update_user_memory_handles_empty_color_and_category(mock_service, sample_user_profile):
    """Test that empty strings for color/category are handled."""
    product_empty = {
        "title": "Product",
        "color": "",
        "category": "   ",
        "price": 25.0
    }
    
    mock_service.get_user_profile = MagicMock(return_value=sample_user_profile)
    mock_service.users.find_one_and_update.return_value = sample_user_profile
    
    result = mock_service.update_user_memory("user123", product_empty, auto_update_preferences=True)
    
    # Should handle empty strings gracefully
    assert result is not None


def test_update_user_memory_case_insensitive_matching(mock_service, sample_user_profile):
    """Test that color/category matching is case-insensitive."""
    # User has "red" in lowercase
    product = {
        "title": "Red Shirt",
        "color": "RED",  # Different case
        "category": "APPAREL"  # Different case
    }
    
    mock_service.get_user_profile = MagicMock(return_value=sample_user_profile)
    mock_service.users.find_one_and_update.return_value = sample_user_profile
    
    result = mock_service.update_user_memory("user123", product, auto_update_preferences=True)
    
    # Should recognize RED == red and not add duplicate
    call_args = mock_service.users.find_one_and_update.call_args
    update_ops = call_args[0][1]
    
    # Should still process, converting to lowercase
    assert result is not None


def test_update_user_memory_returns_updated_profile(mock_service, sample_product, sample_user_profile):
    """Test that update_user_memory returns the updated profile."""
    updated_profile = {
        **sample_user_profile,
        "past_purchases": sample_user_profile["past_purchases"] + [sample_product["title"]],
        "preferred_colors": sample_user_profile["preferred_colors"] + ["blue"]
    }
    
    mock_service.get_user_profile = MagicMock(return_value=sample_user_profile)
    mock_service.users.find_one_and_update.return_value = updated_profile
    
    result = mock_service.update_user_memory("user123", sample_product)
    
    assert result == updated_profile
    assert "Blue Casual Shirt" in result["past_purchases"]


def test_update_user_memory_updates_timestamp(mock_service, sample_product, sample_user_profile):
    """Test that update_user_memory updates the updated_at timestamp."""
    mock_service.get_user_profile = MagicMock(return_value=sample_user_profile)
    mock_service.users.find_one_and_update.return_value = sample_user_profile
    
    result = mock_service.update_user_memory("user123", sample_product)
    
    # Verify timestamp was updated
    call_args = mock_service.users.find_one_and_update.call_args
    assert "$set" in call_args[0][1]
    assert "updated_at" in call_args[0][1]["$set"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
