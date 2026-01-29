# User Profile Service

## Overview

The User Profile Service manages user data in MongoDB, enabling personalized product recommendations based on user preferences, purchase history, and price sensitivity.

## Schema

### UserProfile Collection

```json
{
  "user_id": "USER-001",
  "past_purchases": [
    "Blue Running Shoes",
    "Cotton T-Shirt",
    "Summer Dress"
  ],
  "preferred_colors": ["blue", "black", "gray"],
  "preferred_categories": ["footwear", "apparel"],
  "price_range": {
    "min": 20,
    "max": 200
  },
  "created_at": "2026-01-27T10:30:00Z",
  "updated_at": "2026-01-27T15:45:00Z"
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `user_id` | string | Unique user identifier (indexed, required) |
| `past_purchases` | array | List of purchased product titles |
| `preferred_colors` | array | User's preferred product colors |
| `preferred_categories` | array | User's preferred product categories |
| `price_range` | object | Min/max price limits for products |
| `created_at` | datetime | Profile creation timestamp |
| `updated_at` | datetime | Last update timestamp |

## API Functions

### `create_user_profile()`

Create a new user profile with initial preferences.

**Signature:**
```python
def create_user_profile(
    user_id: str,
    past_purchases: Optional[List[str]] = None,
    preferred_colors: Optional[List[str]] = None,
    preferred_categories: Optional[List[str]] = None,
    price_range: Optional[Dict[str, float]] = None
) -> Dict[str, Any]
```

**Parameters:**
- `user_id`: Unique identifier for the user
- `past_purchases`: List of product titles user has purchased
- `preferred_colors`: Colors user prefers (e.g., ["blue", "black"])
- `preferred_categories`: Categories user prefers (e.g., ["footwear", "apparel"])
- `price_range`: Dictionary with "min" and "max" keys

**Returns:** Created user profile document with MongoDB `_id`

**Raises:** `ValueError` if user already exists

**Example:**
```python
from db.user_service import UserProfileService

service = UserProfileService()
service.connect()

user = service.create_user_profile(
    user_id="USER-001",
    past_purchases=["Blue Shoes", "T-Shirt"],
    preferred_colors=["blue", "black"],
    preferred_categories=["footwear", "apparel"],
    price_range={"min": 20, "max": 200}
)
```

### `get_user_profile()`

Retrieve a user profile by user_id.

**Signature:**
```python
def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]
```

**Parameters:**
- `user_id`: Unique user identifier

**Returns:** User profile document or None if not found

**Example:**
```python
user = service.get_user_profile("USER-001")
if user:
    print(f"Preferred colors: {user['preferred_colors']}")
else:
    print("User not found")
```

### `update_preferences()`

Update user's color, category, and price range preferences (does not affect purchase history).

**Signature:**
```python
def update_preferences(
    user_id: str,
    preferred_colors: Optional[List[str]] = None,
    preferred_categories: Optional[List[str]] = None,
    price_range: Optional[Dict[str, float]] = None
) -> Optional[Dict[str, Any]]
```

**Parameters:**
- `user_id`: Unique user identifier
- `preferred_colors`: New list of preferred colors (replaces existing)
- `preferred_categories`: New list of preferred categories (replaces existing)
- `price_range`: New price range with "min" and "max"

**Returns:** Updated user profile or None if user not found

**Example:**
```python
updated = service.update_preferences(
    user_id="USER-001",
    preferred_colors=["red", "pink"],
    price_range={"min": 50, "max": 300}
)
```

### `add_purchase()`

Add a product to user's purchase history.

**Signature:**
```python
def add_purchase(user_id: str, product_title: str) -> Optional[Dict[str, Any]]
```

**Parameters:**
- `user_id`: Unique user identifier
- `product_title`: Title of purchased product

**Returns:** Updated user profile or None if user not found

**Note:** Uses MongoDB's `$addToSet` operator to prevent duplicate purchases

**Example:**
```python
updated = service.add_purchase("USER-001", "Running Shoes")
```

### `get_all_users()`

Retrieve all user profiles (with optional limit).

**Signature:**
```python
def get_all_users(limit: Optional[int] = None) -> List[Dict[str, Any]]
```

**Parameters:**
- `limit`: Maximum number of users to return (None for all)

**Returns:** List of user profile documents

**Example:**
```python
all_users = service.get_all_users(limit=100)
print(f"Found {len(all_users)} users")
```

### `delete_user_profile()`

Delete a user profile by user_id.

**Signature:**
```python
def delete_user_profile(user_id: str) -> bool
```

**Parameters:**
- `user_id`: Unique user identifier

**Returns:** True if deleted, False if not found

**Example:**
```python
deleted = service.delete_user_profile("USER-001")
```

## Context Manager Usage

The service supports Python's context manager protocol for automatic connection/disconnection:

```python
with UserProfileService() as service:
    user = service.create_user_profile("USER-001")
    print(user)
# Automatically disconnects
```

## Usage Examples

### Complete User Profile Workflow

```python
from db.user_service import UserProfileService

# Initialize service
service = UserProfileService()
service.connect()

# Create new user
user = service.create_user_profile(
    user_id="USER-001",
    past_purchases=["Blue Shoes"],
    preferred_colors=["blue", "black"],
    preferred_categories=["footwear"],
    price_range={"min": 20, "max": 150}
)

# Add a purchase
service.add_purchase("USER-001", "Running Socks")

# Update preferences
service.update_preferences(
    user_id="USER-001",
    price_range={"min": 25, "max": 200}
)

# Retrieve updated profile
user = service.get_user_profile("USER-001")
print(f"Purchases: {user['past_purchases']}")
print(f"New price range: {user['price_range']}")

# Cleanup
service.disconnect()
```

### Integration with Search

User profiles can enhance search by applying user preferences:

```python
user = service.get_user_profile("USER-001")

# Use user's preferred colors and categories as filters
results = search_service.search_by_text(
    query_text="shoes",
    top_k=10,
    color_filter=user['preferred_colors'][0],  # Primary preference
    category_filter=user['preferred_categories'][0]
)

# Further filter by user's price range
filtered_results = [
    r for r in results
    if user['price_range']['min'] <= r.get('price', 0) <= user['price_range']['max']
]
```

## Database Indexes

The service automatically creates the following indexes for optimal performance:

- `user_id`: Unique index for fast lookups
- `created_at`: Index for sorting by registration date

## Error Handling

The service provides clear error messages:

```python
try:
    service.create_user_profile("USER-001")
except ValueError as e:
    print(f"User creation failed: {e}")  # "User profile with user_id 'USER-001' already exists"
except RuntimeError as e:
    print(f"Connection error: {e}")  # "Not connected to MongoDB. Call connect() first."
```

## Testing

Run the test suite:

```bash
python scripts/test_user_service.py
```

Expected output includes:
- User profile creation
- Preference retrieval
- Preference updates
- Purchase additions
- Duplicate detection
- Non-existent user handling
- Context manager functionality
