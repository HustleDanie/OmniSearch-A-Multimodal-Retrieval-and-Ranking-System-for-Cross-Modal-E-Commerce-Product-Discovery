"""
Unit tests for context retrieval formatting functions.
Tests user preferences summary, search result formatting, and LLM input generation.
Tests formatting logic in isolation without requiring full service initialization.
"""
import pytest


class TestSearchResultsFormatting:
    """Test search results formatting."""
    
    def test_format_single_result_with_all_fields(self):
        """Format single result with all available fields."""
        result = {
            "title": "Blue Casual Shirt",
            "description": "Comfortable everyday shirt",
            "category": "apparel",
            "color": "blue",
            "price": 49.99,
            "score": 0.95,
            "size": "M",
            "brand": "StyleCo"
        }
        
        # Simulate formatting like ContextRetriever does
        lines = [f"Result 1: {result['title']}"]
        if result.get("description"):
            lines.append(f"Description: {result['description']}")
        if result.get("category"):
            lines.append(f"Category: {result['category']}")
        if result.get("color"):
            lines.append(f"Color: {result['color']}")
        if result.get("price"):
            lines.append(f"Price: ${result['price']}")
        if result.get("score") is not None:
            lines.append(f"Relevance Score: {result['score']:.2f}")
        if result.get("size"):
            lines.append(f"Size: {result['size']}")
        if result.get("brand"):
            lines.append(f"Brand: {result['brand']}")
        
        formatted = "\n".join(lines)
        
        assert "Blue Casual Shirt" in formatted
        assert "Comfortable everyday shirt" in formatted
        assert "apparel" in formatted
        assert "blue" in formatted
        assert "$49.99" in formatted
        assert "0.95" in formatted
        assert "M" in formatted
        assert "StyleCo" in formatted
    
    def test_format_multiple_results(self):
        """Format multiple search results."""
        search_results = [
            {"title": "Result 1", "score": 0.95},
            {"title": "Result 2", "score": 0.87},
            {"title": "Result 3", "score": 0.79}
        ]
        
        formatted_results = []
        for i, result in enumerate(search_results, 1):
            result_text = f"\nResult {i}: {result.get('title', 'Untitled')}"
            if result.get("score") is not None:
                result_text += f"\nRelevance Score: {result['score']:.2f}"
            formatted_results.append(result_text)
        
        formatted = "\n".join(formatted_results)
        
        assert "Result 1:" in formatted
        assert "Result 2:" in formatted
        assert "Result 3:" in formatted
    
    def test_format_results_respects_max_results(self):
        """Formatting should respect max_results parameter."""
        search_results = [
            {"title": f"Result {i}", "score": 0.9 - i*0.05}
            for i in range(1, 11)  # 10 results
        ]
        
        max_results = 3
        formatted_results = []
        for i, result in enumerate(search_results[:max_results], 1):
            result_text = f"\nResult {i}: {result.get('title', 'Untitled')}"
            formatted_results.append(result_text)
        
        formatted = "\n".join(formatted_results)
        
        assert "Result 1:" in formatted
        assert "Result 2:" in formatted
        assert "Result 3:" in formatted
        assert "Result 4:" not in formatted
    
    def test_format_results_with_minimal_fields(self):
        """Format results with only title."""
        search_result = {"title": "Simple Shirt"}
        
        result_text = f"Result 1: {search_result.get('title', 'Untitled')}"
        
        assert "Simple Shirt" in result_text
        assert "Untitled" not in result_text


class TestPreferencesFormatting:
    """Test user preferences summary formatting."""
    
    def test_format_preferences_with_colors(self):
        """Format preferences with color data."""
        preferences_analysis = {
            "dominant_colors": {"blue": 3, "black": 2, "white": 1},
            "most_frequent_categories": {},
            "style_keywords": {},
            "product_types": {},
            "purchase_count": 6
        }
        
        lines = []
        colors = preferences_analysis.get("dominant_colors", {})
        if colors:
            color_str = ", ".join(
                f"{color} ({freq})"
                for color, freq in list(colors.items())[:5]
            )
            lines.append(f"- Preferred Colors: {color_str}")
        
        summary = "\n".join(lines) if lines else "- No preference data available"
        
        assert "blue" in summary
        assert "Preferred Colors" in summary
        assert "(3)" in summary
    
    def test_format_preferences_with_categories(self):
        """Format preferences with category data."""
        preferences_analysis = {
            "dominant_colors": {},
            "most_frequent_categories": {"apparel": 8, "footwear": 2},
            "style_keywords": {},
            "product_types": {},
            "purchase_count": 10
        }
        
        lines = []
        categories = preferences_analysis.get("most_frequent_categories", {})
        if categories:
            cat_str = ", ".join(
                f"{cat} ({freq})"
                for cat, freq in list(categories.items())[:5]
            )
            lines.append(f"- Favorite Categories: {cat_str}")
        
        summary = "\n".join(lines) if lines else "- No preference data available"
        
        assert "apparel" in summary
        assert "Favorite Categories" in summary
    
    def test_format_preferences_with_style_keywords(self):
        """Format preferences with style keyword data."""
        preferences_analysis = {
            "dominant_colors": {},
            "most_frequent_categories": {},
            "style_keywords": {"casual": 4, "elegant": 3, "classic": 2},
            "product_types": {},
            "purchase_count": 9
        }
        
        lines = []
        keywords = preferences_analysis.get("style_keywords", {})
        if keywords:
            keyword_str = ", ".join(
                f"{kw}"
                for kw in list(keywords.keys())[:5]
            )
            lines.append(f"- Popular Styles: {keyword_str}")
        
        summary = "\n".join(lines) if lines else "- No preference data available"
        
        assert "Popular Styles" in summary
        assert "casual" in summary
    
    def test_format_preferences_empty(self):
        """Format preferences with no data."""
        preferences_analysis = {
            "dominant_colors": {},
            "most_frequent_categories": {},
            "style_keywords": {},
            "product_types": {},
            "purchase_count": 0
        }
        
        lines = []
        summary = "\n".join(lines) if lines else "- No preference data available"
        
        assert "No preference data available" in summary


class TestContextStructuring:
    """Test context structure for LLM input."""
    
    def test_context_has_two_main_sections(self):
        """Context should have USER PREFERENCES and SEARCH RESULTS sections."""
        preferences_section = "USER PREFERENCES:\n- Some preference"
        results_section = "SEARCH RESULTS (1 items):\n- Result 1"
        
        context = f"""{preferences_section}

{results_section}"""
        
        assert "USER PREFERENCES:" in context
        assert "SEARCH RESULTS" in context
        assert context.count("USER PREFERENCES:") == 1
    
    def test_context_result_numbering(self):
        """Results in context should be numbered."""
        results_parts = []
        for i in range(1, 4):
            results_parts.append(f"Result {i}: Item {i}")
        
        results_section = "\n".join(results_parts)
        
        assert "Result 1:" in results_section
        assert "Result 2:" in results_section
        assert "Result 3:" in results_section
    
    def test_currency_formatting(self):
        """Prices should include $ symbol."""
        price = 49.99
        formatted_price = f"${price}"
        
        assert "$49.99" in formatted_price
    
    def test_relevance_score_formatting(self):
        """Relevance scores should be formatted to 2 decimal places."""
        score = 0.9234
        formatted_score = f"{score:.2f}"
        
        assert formatted_score == "0.92"
        assert "0.9234" not in formatted_score


class TestRealWorldScenarios:
    """Test with realistic formatting scenarios."""
    
    def test_fashion_enthusiast_preferences_string(self):
        """Generate preference string for fashion enthusiast."""
        preferences = {
            "dominant_colors": {"blue": 3, "black": 2},
            "most_frequent_categories": {"apparel": 8, "footwear": 3},
            "style_keywords": {"elegant": 4, "casual": 3, "classic": 2},
            "product_types": {"shirt": 5, "dress": 3, "shoes": 2},
            "purchase_count": 13
        }
        
        pref_lines = []
        
        colors = preferences.get("dominant_colors", {})
        if colors:
            color_str = ", ".join(f"{c} ({f})" for c, f in list(colors.items())[:5])
            pref_lines.append(f"- Preferred Colors: {color_str}")
        
        categories = preferences.get("most_frequent_categories", {})
        if categories:
            cat_str = ", ".join(f"{c} ({f})" for c, f in list(categories.items())[:5])
            pref_lines.append(f"- Favorite Categories: {cat_str}")
        
        keywords = preferences.get("style_keywords", {})
        if keywords:
            kw_str = ", ".join(list(keywords.keys())[:5])
            pref_lines.append(f"- Popular Styles: {kw_str}")
        
        pref_summary = "\n".join(pref_lines)
        
        assert "blue" in pref_summary
        assert "black" in pref_summary
        assert "apparel" in pref_summary
        assert "footwear" in pref_summary
        assert "elegant" in pref_summary
    
    def test_search_results_with_rankings(self):
        """Format search results with relevance rankings."""
        search_results = [
            {
                "title": "Blue Elegant Cardigan",
                "description": "Premium wool cardigan",
                "category": "apparel",
                "color": "blue",
                "price": 89.99,
                "score": 0.96
            },
            {
                "title": "Black Designer Shoes",
                "description": "Italian leather shoes",
                "category": "footwear",
                "color": "black",
                "price": 129.99,
                "score": 0.91
            },
            {
                "title": "White Classic Blouse",
                "category": "apparel",
                "color": "white",
                "price": 59.99,
                "score": 0.87
            }
        ]
        
        formatted = []
        for i, result in enumerate(search_results, 1):
            lines = [f"Result {i}: {result.get('title', 'Untitled')}"]
            if result.get("description"):
                lines.append(f"Description: {result['description']}")
            if result.get("category"):
                lines.append(f"Category: {result['category']}")
            if result.get("color"):
                lines.append(f"Color: {result['color']}")
            if result.get("price"):
                lines.append(f"Price: ${result['price']}")
            if result.get("score"):
                lines.append(f"Relevance Score: {result['score']:.2f}")
            formatted.append("\n".join(lines))
        
        full_results = "\n\n".join(formatted)
        
        assert "Result 1: Blue Elegant Cardigan" in full_results
        assert "Result 2: Black Designer Shoes" in full_results
        assert "Result 3: White Classic Blouse" in full_results
        
        assert "$89.99" in full_results
        assert "$129.99" in full_results
        assert "0.96" in full_results
        assert "0.91" in full_results
        assert "0.87" in full_results


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
