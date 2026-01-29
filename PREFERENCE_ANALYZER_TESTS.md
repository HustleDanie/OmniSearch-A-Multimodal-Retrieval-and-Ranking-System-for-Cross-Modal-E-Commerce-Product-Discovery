# PreferenceAnalyzer Unit Tests

## Test Summary

**Total Tests: 31 | Status: ✅ ALL PASSING**

Created comprehensive test suite for the preference analysis module with 8 test classes covering all functionality.

## Test Coverage

### 1. Color Extraction (7 tests)
Tests color extraction and frequency analysis from product titles.

- **test_single_color_extraction**: Extract single color from title
- **test_multiple_colors_in_titles**: Extract colors from multiple titles and count frequencies
- **test_case_insensitive_color_matching**: Case-insensitive matching (BLUE, Blue, blue all match)
- **test_color_boundaries**: Word-boundary regex prevents matching "blue" in "blueberry"
- **test_empty_title_list**: Empty input returns empty dict
- **test_common_colors**: Test all 42 common color keywords (red, green, blue, navy, etc.)
- **test_sorting_by_frequency**: Colors sorted by frequency (most common first)

### 2. Category Analysis (4 tests)
Tests category counting and frequency analysis.

- **test_category_counting**: Count category frequencies
- **test_case_insensitive_categories**: Categories normalized to lowercase
- **test_sorting_categories**: Categories sorted by frequency
- **test_empty_categories**: Empty input returns empty dict

### 3. Style Keyword Extraction (5 tests)
Tests detection of fashion style descriptors.

- **test_single_keyword_extraction**: Extract single style keyword
- **test_multiple_keywords**: Extract multiple keywords from titles
- **test_keyword_boundaries**: Word-boundary matching for accurate detection
- **test_no_style_keywords**: Titles without keywords return empty dict
- **test_common_style_keywords**: Test common keywords (casual, formal, boho, trendy, vintage, etc.)

### 4. Product Type Extraction (2 tests)
Tests identification of product types (shirt, shoes, dress, etc.).

- **test_product_type_identification**: Identify product types from titles
- **test_multiple_product_types**: Count multiple product types

### 5. Full Analysis (4 tests)
Tests complete preference analysis pipeline.

- **test_full_preference_analysis**: Complete analysis with titles and categories
- **test_analysis_with_no_purchases**: Empty purchase list returns proper defaults
- **test_top_n_limiting**: Results limited to top N items
- **test_minimum_frequency_filtering**: Low-frequency items filtered out

### 6. Convenience Methods (5 tests)
Tests quick-access methods for individual analyses.

- **test_get_top_colors**: Get top N colors
- **test_get_top_categories**: Get top N categories
- **test_get_top_style_keywords**: Get top N style keywords
- **test_infer_style_profile**: Generate style profile description
- **test_infer_style_profile_empty**: Empty purchases return "Unknown"

### 7. Analyzer Configuration (2 tests)
Tests configurable parameters.

- **test_custom_top_n**: Custom top_n parameter limits results
- **test_custom_min_frequency**: Custom min_frequency filters items

### 8. Real-World Scenarios (3 tests)
Tests with realistic user purchase data.

- **test_fashion_enthusiast**: Analyze fashion-focused user (multiple styles, colors)
- **test_minimalist_style**: Detect minimalist style preference
- **test_mixed_preferences**: Analyze user with diverse preferences

## Key Testing Aspects

### 1. **Word Boundary Matching**
All keyword extraction uses word-boundary regex (`\b...\b`) to prevent:
- "blue" matching in "blueberry"
- "red" matching in "reddish"
- "formal" matching in "formality"

### 2. **Frequency-Based Ranking**
Results sorted by frequency in descending order:
- Most purchased colors first
- Most common categories first  
- Most mentioned style keywords first

### 3. **Case Insensitivity**
All matching is case-insensitive:
- "Blue", "BLUE", "blue" all match the same keyword
- Categories normalized to lowercase

### 4. **Configurable Limits**
- `top_n`: Limit results to top N items (default: 5)
- `min_frequency`: Exclude items below frequency threshold (default: 1)

### 5. **Comprehensive Keyword Databases**
- **Colors**: 42 common colors (red, blue, navy, teal, rose, etc.)
- **Style Keywords**: 41 fashion style descriptors (casual, formal, elegant, boho, vintage, minimalist, trendy, etc.)
- **Product Types**: 40+ garment types (shirt, dress, shoes, pants, jacket, etc.)

## Test Execution

```bash
pytest tests/test_preference_analyzer.py -v
```

### Results
```
31 passed in 0.19s
```

## Integration Points

The preference analyzer integrates with:

1. **UserProfileService**: Analyzes `past_purchases` list from user profiles
2. **API Routes**: Can be exposed via endpoint `/user/{user_id}/preferences/analyze`
3. **Personalization**: Used for personalized product recommendations

## Example Usage

```python
from services.preference_analyzer import PreferenceAnalyzer

analyzer = PreferenceAnalyzer(top_n=5, min_frequency=1)

# Single analysis
purchases = [
    "Blue Casual Shirt",
    "Blue Elegant Dress",
    "Black Classic Pants"
]
categories = ["apparel", "apparel", "apparel"]

analysis = analyzer.analyze_preferences(purchases, categories)
# Returns: {
#     "dominant_colors": {"blue": 2, "black": 1},
#     "most_frequent_categories": {"apparel": 3},
#     "style_keywords": {"casual": 1, "elegant": 1, "classic": 1},
#     "product_types": {"shirt": 1, "dress": 1, "pants": 1},
#     "purchase_count": 3,
#     "unique_colors": 2,
#     "unique_categories": 1,
#     "unique_keywords": 3
# }

# Quick access methods
top_colors = analyzer.get_top_colors(purchases, n=2)
style_profile = analyzer.infer_style_profile(purchases)
```

## Code Quality

- **Coverage**: All public methods tested
- **Edge Cases**: Empty inputs, single items, duplicates
- **Realistic Data**: Fashion product titles and categories
- **Validation**: Regex patterns, frequency counting, sorting
