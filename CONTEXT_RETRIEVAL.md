# Context Retrieval for LLM Input

The `retrieve_context()` function retrieves user preferences and search results formatted as structured text suitable for LLM prompt generation.

## Overview

- **Module**: [services/context_retrieval.py](services/context_retrieval.py)
- **Main Function**: `retrieve_context(user_id, search_results, max_results=5)`
- **Class**: `ContextRetriever`
- **Purpose**: Generate contextualized LLM input from user preferences + search results

## Function Signature

```python
def retrieve_context(
    user_id: str,
    search_results: List[Dict[str, Any]],
    max_results: int = 5
) -> str:
    """
    Retrieve user preferences and search results formatted for LLM input.
    
    Args:
        user_id: MongoDB user ID
        search_results: List of search result dicts with:
            - title (str)
            - description (str, optional)
            - color (str, optional)
            - category (str, optional)
            - score (float, optional)
            - price (float, optional)
            - brand (str, optional)
            - size (str, optional)
        max_results: Maximum search results to include (default: 5)
    
    Returns:
        Structured text formatted for LLM consumption
    """
```

## Usage Example

```python
from services import retrieve_context

# Fetch search results from your search service
search_results = [
    {
        "title": "Blue Casual Cotton Shirt",
        "description": "Comfortable everyday shirt with flexible fabric",
        "color": "blue",
        "category": "apparel",
        "price": 49.99,
        "score": 0.96,
        "brand": "StyleCo"
    },
    {
        "title": "Black Elegant Blazer",
        "description": "Professional wool blend blazer",
        "color": "black",
        "category": "apparel",
        "price": 129.99,
        "score": 0.92,
        "brand": "Premium Wear"
    },
    # ... more results
]

# Get context for a user
context = retrieve_context(
    user_id="user_123",
    search_results=search_results,
    max_results=5
)

# Use in LLM prompt
prompt = f"""
Based on this user's preferences and purchase history, 
explain why these products match their style:

{context}

Provide personalized recommendations considering their color 
preferences, favorite categories, and style profile.
"""

response = llm.generate(prompt)
```

## Output Format

The returned context string has two main sections:

### 1. USER PREFERENCES
Contains:
- **Preferred Colors**: Top colors from purchase history with frequency
- **Favorite Categories**: Most frequent product categories
- **Style Profile**: Inferred style description (e.g., "Classic elegant style with casual comfort elements")
- **Popular Styles**: Most mentioned style keywords (casual, elegant, formal, etc.)
- **Price Range**: From user profile preferences (if set)
- **Size Preference**: From user profile (if set)

### 2. SEARCH RESULTS
Numbered list of products with:
- **Title**: Product name
- **Description**: Product description
- **Category**: Product category
- **Color**: Primary color
- **Price**: Formatted with $ symbol
- **Relevance Score**: Formatted to 2 decimal places (0.00-1.00)
- **Brand**: Product brand (if available)
- **Size**: Size info (if available)

### Example Output

```
USER PREFERENCES:
- Preferred Colors: blue (3), black (2), white (1)
- Favorite Categories: apparel (8), footwear (2)
- Style Profile: Classic elegant style with casual comfort elements
- Popular Styles: casual, elegant, comfortable, classic
- Price Range: $50-$200
- Size Preference: Medium

SEARCH RESULTS (3 items):

Result 1: Blue Elegant Cardigan
Description: Premium wool cardigan with intricate knit pattern
Category: apparel
Color: blue
Price: $89.99
Relevance Score: 0.96
Brand: StyleCo

Result 2: Black Designer Shoes
Description: Italian leather shoes with premium comfort sole
Category: footwear
Color: black
Price: $129.99
Relevance Score: 0.92
Brand: Premium Wear

Result 3: White Casual T-Shirt
Category: apparel
Color: white
Price: $34.99
Relevance Score: 0.88
```

## Features

### Smart Formatting
- Prices formatted with `$` symbol
- Relevance scores formatted to 2 decimal places
- Results numbered sequentially (Result 1:, Result 2:, etc.)
- Optional fields omitted if not present

### User Preference Inference
- Extracts dominant colors from purchase history
- Identifies most frequent product categories
- Detects style keywords from product titles
- Infers overall style profile
- Includes price range and size preferences from user profile

### LLM-Friendly Structure
- Clear section headers (USER PREFERENCES, SEARCH RESULTS)
- Consistent field formatting
- Human-readable text suitable for language models
- Respects max_results parameter to control context size

## Integration Points

### 1. Search Results Integration
```python
from api.search_endpoint import search_products
from services import retrieve_context

# Get search results from multimodal search
search_results = search_products(
    query="blue casual shirts",
    user_id="user_123"
)

# Get formatted context
context = retrieve_context("user_123", search_results)
```

### 2. LLM Recommendation Generation
```python
from services import retrieve_context
from llm_service import LLMClient

context = retrieve_context(user_id, search_results)

prompt = f"""
Given this user's style preferences:

{context}

Recommend the best product and explain why it matches their preferences.
"""

recommendation = llm_client.generate(prompt)
```

### 3. LLM-Based Personalization
```python
context = retrieve_context(user_id, search_results)

prompts = [
    f"{context}\n\nCreate a catchy product description for the top result",
    f"{context}\n\nExplain which product best matches this user's style",
    f"{context}\n\nWhat accessories would complement these products?"
]

responses = [llm_client.generate(p) for p in prompts]
```

## Testing

Run tests with:
```bash
pytest tests/test_context_retrieval.py -v
```

**Test Coverage** (14 tests):
- Search results formatting (4 tests)
- Preferences formatting (4 tests)
- Context structure (4 tests)
- Real-world scenarios (2 tests)

All tests verify:
✓ Correct field formatting
✓ Optional field handling
✓ Result limiting (max_results)
✓ Preference extraction
✓ LLM-friendly output structure

## Performance Notes

- **Lazy Loading**: Services (PreferenceAnalyzer, UserProfileService) load on demand
- **Database Access**: Makes MongoDB query for user profile (can be cached)
- **In-Memory**: All formatting done in memory, no additional I/O
- **Time Complexity**: O(n) where n = number of search results

Typical execution time: <100ms for 5 results with user profile

## Error Handling

- **Missing User Profile**: Returns generic context with just search results
- **Empty Search Results**: Returns context with "No search results available"
- **Invalid User ID**: Gracefully handled, returns empty preferences
- **Missing Fields**: Optional fields silently omitted from output

## Configuration

Customize via `ContextRetriever` initialization:
```python
retriever = ContextRetriever()

# Access the preference analyzer
# to control color/keyword extraction
retriever.preference_analyzer.top_n = 10
retriever.preference_analyzer.min_frequency = 2
```

## Related Modules

- **PreferenceAnalyzer** ([services/preference_analyzer.py](services/preference_analyzer.py)): Extracts colors, categories, and keywords from purchase history
- **UserProfileService** ([db/user_service.py](db/user_service.py)): Manages user profiles and preference storage
- **ProductSearchService** ([services/search_service.py](services/search_service.py)): Returns search results to format
