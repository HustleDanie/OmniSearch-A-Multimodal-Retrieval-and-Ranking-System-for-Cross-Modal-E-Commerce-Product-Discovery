# update_user_memory() - User Memory Update Function

## Overview

The `update_user_memory()` function updates user preferences and purchase history after a recommendation is clicked or purchased. It intelligently extracts product attributes and updates the user's profile for better future recommendations.

## Function Signature

```python
def update_user_memory(
    self, 
    user_id: str, 
    product: Dict[str, Any],
    auto_update_preferences: bool = True
) -> Optional[Dict[str, Any]]
```

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `user_id` | str | Yes | - | Unique user identifier |
| `product` | Dict[str, Any] | Yes | - | Product dictionary with title, color, category, price |
| `auto_update_preferences` | bool | No | True | Automatically update preferences from product attributes |

## Product Dictionary Format

```python
{
    "title": str,           # Required - Product name/title
    "color": str,           # Optional - Product color
    "category": str,        # Optional - Product category
    "price": float,         # Optional - Product price
    "description": str,     # Optional - Product description
    # ... other fields
}
```

## What It Does

### 1. Adds to Purchase History
- Appends product title to user's `past_purchases` array
- Uses `$addToSet` to avoid duplicates
- Updates `updated_at` timestamp

### 2. Updates Preferences (if `auto_update_preferences=True`)

**Color Preferences:**
- Extracts product color
- Adds to `preferred_colors` if not already present
- Case-insensitive matching (e.g., "Blue" → "blue")

**Category Preferences:**
- Extracts product category
- Adds to `preferred_categories` if not already present
- Case-insensitive matching

**Price Range:**
- Expands user's price range if product is outside current range
- Updates `min` if product price is lower
- Updates `max` if product price is higher

### 3. Creates User if Not Exists
- If user profile doesn't exist, creates a new one
- Initializes with default preferences
- Then proceeds with the update

## Return Value

Returns the updated user profile dictionary or `None` if update failed:

```python
{
    "user_id": "user123",
    "past_purchases": ["Product 1", "Product 2", "New Product"],
    "preferred_colors": ["blue", "red", "green"],
    "preferred_categories": ["apparel", "footwear"],
    "price_range": {"min": 20.0, "max": 150.0},
    "created_at": datetime(...),
    "updated_at": datetime(...)
}
```

## Usage Examples

### Example 1: Basic Usage (After Purchase)

```python
from db.user_service import UserProfileService

# Initialize service
service = UserProfileService()
service.connect()

# Product that was purchased
product = {
    "title": "Blue Casual Shirt",
    "color": "blue",
    "category": "apparel",
    "price": 49.99
}

# Update user memory
updated_profile = service.update_user_memory("user123", product)

if updated_profile:
    print(f"✓ Updated profile for {updated_profile['user_id']}")
    print(f"  Purchases: {len(updated_profile['past_purchases'])}")
    print(f"  Colors: {updated_profile['preferred_colors']}")

service.disconnect()
```

### Example 2: After Recommendation Click

```python
# After user clicks a recommendation
recommendation = {
    "title": "Black Formal Blazer",
    "color": "black",
    "category": "apparel",
    "price": 129.99
}

# Track the interaction
service.update_user_memory("user123", recommendation)
```

### Example 3: Without Auto-Updating Preferences

```python
# Just add to purchase history, don't update preferences
product = {
    "title": "Gift Item - Red Scarf",
    "color": "red",
    "category": "accessories",
    "price": 25.00
}

# Disable auto-update if this was a gift (not user's preference)
service.update_user_memory(
    "user123", 
    product, 
    auto_update_preferences=False
)
```

### Example 4: Minimal Product Info

```python
# Works with minimal product info (only title required)
product = {
    "title": "Product Name"
    # No color, category, or price
}

# Still updates purchase history
service.update_user_memory("user123", product)
```

### Example 5: Integration with Recommendation Endpoint

```python
# In your recommendation endpoint after user interaction
from db import UserProfileService

@app.post("/recommendation/track")
async def track_recommendation(user_id: str, product_id: str, action: str):
    """Track when user clicks or purchases a recommendation."""
    
    # Get product details
    product = get_product_by_id(product_id)  # Your function
    
    # Update user memory
    service = UserProfileService()
    service.connect()
    
    updated_profile = service.update_user_memory(user_id, product)
    
    service.disconnect()
    
    return {
        "status": "success",
        "action": action,
        "updated_preferences": {
            "colors": updated_profile.get("preferred_colors", []),
            "categories": updated_profile.get("preferred_categories", [])
        }
    }
```

### Example 6: Batch Updates

```python
# Update multiple purchases at once
purchased_products = [
    {"title": "Product 1", "color": "blue", "category": "apparel", "price": 50},
    {"title": "Product 2", "color": "red", "category": "footwear", "price": 80},
    {"title": "Product 3", "color": "green", "category": "apparel", "price": 45}
]

service = UserProfileService()
service.connect()

for product in purchased_products:
    service.update_user_memory("user123", product)

service.disconnect()
```

## Error Handling

### ValueError: Missing Title

```python
product = {"color": "blue"}  # Missing title

try:
    service.update_user_memory("user123", product)
except ValueError as e:
    print(f"Error: {e}")  # "Product must have 'title' field"
```

### RuntimeError: Not Connected

```python
service = UserProfileService()
# Forgot to call connect()

try:
    service.update_user_memory("user123", product)
except RuntimeError as e:
    print(f"Error: {e}")  # "Not connected to MongoDB. Call connect() first."
```

### Handle User Not Found

```python
# Function handles this automatically by creating new user
updated = service.update_user_memory("newuser999", product)

if updated:
    print("User created and updated")
```

## Best Practices

### 1. Always Connect First
```python
service = UserProfileService()
service.connect()
try:
    service.update_user_memory(user_id, product)
finally:
    service.disconnect()
```

### 2. Use Context Manager
```python
with UserProfileService() as service:
    service.update_user_memory(user_id, product)
```

### 3. Validate Product Data
```python
if "title" in product and product["title"]:
    service.update_user_memory(user_id, product)
else:
    print("Product missing required title field")
```

### 4. Handle Return Value
```python
updated = service.update_user_memory(user_id, product)

if updated:
    # Success
    log_user_activity(user_id, "preferences_updated")
else:
    # Failed (shouldn't happen if user exists/created)
    log_error(user_id, "memory_update_failed")
```

### 5. Consider Auto-Update Flag
```python
# For user's own purchases - update preferences
service.update_user_memory(user_id, product, auto_update_preferences=True)

# For gifts or returns - don't update preferences
service.update_user_memory(user_id, product, auto_update_preferences=False)
```

## Integration with Agent Endpoint

```python
# In api/agent.py - After recommendation is acted upon

@router.post("/recommendation/feedback")
async def recommendation_feedback(
    user_id: str = Form(...),
    product_id: str = Form(...),
    action: str = Form(...)  # "clicked", "purchased", etc.
):
    """Track user interaction with recommendations."""
    
    # Get product details from search results or database
    product = {
        "title": "Retrieved Product Title",
        "color": "blue",
        "category": "apparel",
        "price": 49.99
    }
    
    # Update user memory
    with UserProfileService() as service:
        updated = service.update_user_memory(user_id, product)
    
    return {
        "status": "success",
        "user_id": user_id,
        "action": action,
        "preferences_updated": bool(updated)
    }
```

## Performance Considerations

- **Single Operation**: Updates happen in one MongoDB operation
- **Atomic Updates**: Uses `$addToSet` and `$set` for atomic operations
- **Minimal Queries**: Only fetches user profile once
- **Auto-Creation**: Creates user if not found (no extra round-trip)
- **Typical Time**: 10-50ms for update operation

## Testing

Run the tests:
```bash
pytest tests/test_update_user_memory.py -v
```

All 13 tests cover:
- ✅ Adding purchases
- ✅ Updating color preferences
- ✅ Updating category preferences
- ✅ Expanding price range
- ✅ Auto-update flag behavior
- ✅ User creation if not exists
- ✅ Error handling (missing title, not connected)
- ✅ Missing optional fields
- ✅ Empty values handling
- ✅ Case-insensitive matching
- ✅ Return value validation
- ✅ Timestamp updates

## Future Enhancements

- [ ] Confidence scores for preferences
- [ ] Weighted preferences based on frequency
- [ ] Time-decay for old purchases
- [ ] Preference removal (if user dislikes)
- [ ] Preference explanation/reasoning
- [ ] Batch update optimization
- [ ] Preference change notifications
- [ ] Analytics on preference evolution
