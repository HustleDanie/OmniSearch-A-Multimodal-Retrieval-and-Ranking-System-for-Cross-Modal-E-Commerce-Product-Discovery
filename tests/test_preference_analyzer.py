"""
Unit tests for the preference analyzer module.
Tests color extraction, category analysis, and style keyword detection.
"""
import pytest
import sys
import importlib.util
from pathlib import Path

# Load preference_analyzer module directly to avoid torch dependency
spec = importlib.util.spec_from_file_location(
    "preference_analyzer",
    Path(__file__).parent.parent / "services" / "preference_analyzer.py"
)
preference_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preference_module)
PreferenceAnalyzer = preference_module.PreferenceAnalyzer


class TestColorExtraction:
    """Test color extraction from product titles."""
    
    def test_single_color_extraction(self):
        """Extract single color from title."""
        analyzer = PreferenceAnalyzer()
        titles = ["Blue Cotton Shirt"]
        
        colors = analyzer.extract_colors(titles)
        
        assert "blue" in colors
        assert colors["blue"] == 1
    
    def test_multiple_colors_in_titles(self):
        """Extract multiple colors from different titles."""
        analyzer = PreferenceAnalyzer()
        titles = [
            "Blue Running Shoes",
            "Black Jeans",
            "Blue T-Shirt",
            "Gray Sweater"
        ]
        
        colors = analyzer.extract_colors(titles)
        
        assert colors["blue"] == 2
        assert colors["black"] == 1
        assert colors["gray"] == 1
    
    def test_case_insensitive_color_matching(self):
        """Colors should match regardless of case."""
        analyzer = PreferenceAnalyzer()
        titles = [
            "BLUE Shirt",
            "Blue Pants",
            "blue shoes"
        ]
        
        colors = analyzer.extract_colors(titles)
        
        assert colors["blue"] == 3
    
    def test_color_boundaries(self):
        """Color matching should use word boundaries."""
        analyzer = PreferenceAnalyzer()
        titles = [
            "Blueberry Pie",  # Should not match "blue"
            "Blue Shirt",     # Should match
            "Reddish Dress"   # Should not match "red"
        ]
        
        colors = analyzer.extract_colors(titles)
        
        assert colors.get("blue") == 1  # Only "Blue Shirt"
        assert "red" not in colors
    
    def test_empty_title_list(self):
        """Empty title list should return empty dict."""
        analyzer = PreferenceAnalyzer()
        colors = analyzer.extract_colors([])
        
        assert colors == {}
    
    def test_common_colors(self):
        """Test extraction of common colors."""
        analyzer = PreferenceAnalyzer()
        titles = [
            "Red Dress",
            "Green Jacket",
            "Yellow Shirt",
            "Purple Shoes"
        ]
        
        colors = analyzer.extract_colors(titles)
        
        assert len(colors) == 4
        assert all(color in colors for color in ["red", "green", "yellow", "purple"])
    
    def test_sorting_by_frequency(self):
        """Colors should be sorted by frequency."""
        analyzer = PreferenceAnalyzer()
        titles = [
            "Black Shirt",
            "Black Pants",
            "Black Shoes",
            "Blue Tie",
            "Blue Scarf"
        ]
        
        colors = analyzer.extract_colors(titles)
        color_list = list(colors.keys())
        
        # Black should be first (frequency 3) before Blue (frequency 2)
        assert color_list.index("black") < color_list.index("blue")
        assert colors["black"] == 3
        assert colors["blue"] == 2


class TestCategoryAnalysis:
    """Test category extraction and analysis."""
    
    def test_category_counting(self):
        """Count category frequencies."""
        analyzer = PreferenceAnalyzer()
        categories = ["apparel", "footwear", "apparel", "apparel", "footwear"]
        
        result = analyzer.extract_categories(categories)
        
        assert result["apparel"] == 3
        assert result["footwear"] == 2
    
    def test_case_insensitive_categories(self):
        """Categories should be normalized to lowercase."""
        analyzer = PreferenceAnalyzer()
        categories = ["Apparel", "FOOTWEAR", "apparel"]
        
        result = analyzer.extract_categories(categories)
        
        assert "apparel" in result
        assert result["apparel"] == 2
        assert "FOOTWEAR" not in result
        assert "footwear" in result
    
    def test_sorting_categories(self):
        """Categories should be sorted by frequency."""
        analyzer = PreferenceAnalyzer()
        categories = [
            "shoes",
            "shoes",
            "shoes",
            "bags",
            "bags",
            "accessories"
        ]
        
        result = analyzer.extract_categories(categories)
        cat_list = list(result.keys())
        
        assert cat_list[0] == "shoes"
        assert cat_list[1] == "bags"
        assert cat_list[2] == "accessories"
    
    def test_empty_categories(self):
        """Empty category list should return empty dict."""
        analyzer = PreferenceAnalyzer()
        result = analyzer.extract_categories([])
        
        assert result == {}


class TestStyleKeywordExtraction:
    """Test style keyword detection from titles."""
    
    def test_single_keyword_extraction(self):
        """Extract single style keyword."""
        analyzer = PreferenceAnalyzer()
        titles = ["Casual Cotton Shirt"]
        
        keywords = analyzer.extract_style_keywords(titles)
        
        assert "casual" in keywords
        assert keywords["casual"] == 1
    
    def test_multiple_keywords(self):
        """Extract multiple style keywords from titles."""
        analyzer = PreferenceAnalyzer()
        titles = [
            "Elegant formal dress",
            "Casual comfortable jeans",
            "Classic elegant blazer"
        ]
        
        keywords = analyzer.extract_style_keywords(titles)
        
        assert keywords["elegant"] == 2
        assert keywords["formal"] == 1
        assert keywords["casual"] == 1
        assert keywords["comfortable"] == 1
        assert keywords["classic"] == 1
    
    def test_keyword_boundaries(self):
        """Keywords should use word boundaries."""
        analyzer = PreferenceAnalyzer()
        titles = [
            "Formal Wear",      # Should match "formal"
            "Formality Event"   # Should not match "formal"
        ]
        
        keywords = analyzer.extract_style_keywords(titles)
        
        assert keywords.get("formal") == 1
    
    def test_no_style_keywords(self):
        """Titles without style keywords return empty dict."""
        analyzer = PreferenceAnalyzer()
        titles = ["Product A", "Item B", "Thing C"]
        
        keywords = analyzer.extract_style_keywords(titles)
        
        assert keywords == {}
    
    def test_common_style_keywords(self):
        """Test detection of common style keywords."""
        analyzer = PreferenceAnalyzer()
        titles = [
            "Boho chic dress",
            "Trendy minimalist look",
            "Vintage bohemian scarf"
        ]
        
        keywords = analyzer.extract_style_keywords(titles)
        
        assert "boho" in keywords or "bohemian" in keywords
        assert "chic" in keywords
        assert "trendy" in keywords


class TestProductTypeExtraction:
    """Test product type detection."""
    
    def test_product_type_identification(self):
        """Identify product types from titles."""
        analyzer = PreferenceAnalyzer()
        titles = [
            "Blue Cotton Shirt",
            "Black Leather Shoes",
            "Red Summer Dress"
        ]
        
        types = analyzer.extract_product_types(titles)
        
        assert types.get("shirt") == 1
        assert types.get("shoes") == 1
        assert types.get("dress") == 1
    
    def test_multiple_product_types(self):
        """Count multiple product types."""
        analyzer = PreferenceAnalyzer()
        titles = [
            "Casual shirt",
            "Formal shirt",
            "Running shoes",
            "Athletic shoes",
            "Evening dress"
        ]
        
        types = analyzer.extract_product_types(titles)
        
        assert types.get("shirt") == 2
        assert types.get("shoes") == 2
        assert types.get("dress") == 1


class TestFullAnalysis:
    """Test complete preference analysis."""
    
    def test_full_preference_analysis(self):
        """Complete analysis of user preferences."""
        analyzer = PreferenceAnalyzer()
        purchases = [
            "Blue Casual Shirt",
            "Blue Elegant Dress",
            "Black Classic Pants",
            "White Comfortable T-Shirt"
        ]
        categories = ["apparel", "apparel", "apparel", "apparel"]
        
        analysis = analyzer.analyze_preferences(purchases, categories)
        
        assert analysis["purchase_count"] == 4
        assert "blue" in analysis["dominant_colors"]
        assert "apparel" in analysis["most_frequent_categories"]
        assert analysis["unique_colors"] > 0
        assert analysis["unique_keywords"] > 0
    
    def test_analysis_with_no_purchases(self):
        """Analysis of empty purchase list returns defaults."""
        analyzer = PreferenceAnalyzer()
        
        analysis = analyzer.analyze_preferences([])
        
        assert analysis["purchase_count"] == 0
        assert analysis["dominant_colors"] == {}
        assert analysis["most_frequent_categories"] == {}
    
    def test_top_n_limiting(self):
        """Results should be limited to top N."""
        analyzer = PreferenceAnalyzer(top_n=2)
        purchases = [
            "Blue Shirt",
            "Blue Pants",
            "Blue Shoes",
            "Black Jacket",
            "Black Tie",
            "Red Scarf"
        ]
        
        analysis = analyzer.analyze_preferences(purchases)
        
        # Should only have top 2
        assert len(analysis["dominant_colors"]) == 2
        assert "blue" in analysis["dominant_colors"]
        assert "black" in analysis["dominant_colors"]
        assert "red" not in analysis["dominant_colors"]
    
    def test_minimum_frequency_filtering(self):
        """Items below minimum frequency should be excluded."""
        analyzer = PreferenceAnalyzer(min_frequency=2)
        purchases = [
            "Blue Shirt",
            "Blue Pants",
            "Red Dress"  # Only appears once
        ]
        
        analysis = analyzer.analyze_preferences(purchases)
        
        assert "blue" in analysis["dominant_colors"]
        assert "red" not in analysis["dominant_colors"]


class TestConvenienceMethods:
    """Test convenience methods for quick access."""
    
    def test_get_top_colors(self):
        """Get top N colors quickly."""
        analyzer = PreferenceAnalyzer()
        titles = [
            "Blue Shirt",
            "Blue Pants",
            "Black Jacket",
            "Red Dress"
        ]
        
        top_colors = analyzer.get_top_colors(titles, n=2)
        
        assert len(top_colors) <= 2
        assert "blue" in top_colors
    
    def test_get_top_categories(self):
        """Get top N categories quickly."""
        analyzer = PreferenceAnalyzer()
        categories = [
            "shoes", "shoes", "shoes",
            "bags", "bags",
            "hats"
        ]
        
        top_cats = analyzer.get_top_categories(categories, n=2)
        
        assert len(top_cats) <= 2
        assert "shoes" in top_cats
        assert "bags" in top_cats
    
    def test_get_top_style_keywords(self):
        """Get top N style keywords quickly."""
        analyzer = PreferenceAnalyzer()
        titles = [
            "Casual comfortable shirt",
            "Casual trendy dress",
            "Classic elegant jacket"
        ]
        
        top_keywords = analyzer.get_top_style_keywords(titles, n=3)
        
        assert len(top_keywords) <= 3
        assert "casual" in top_keywords
    
    def test_infer_style_profile(self):
        """Infer overall style profile."""
        analyzer = PreferenceAnalyzer()
        purchases = [
            "Casual comfortable shirt",
            "Casual trendy dress",
            "Classic elegant jacket"
        ]
        
        profile = analyzer.infer_style_profile(purchases)
        
        assert profile != "Unknown"
        assert len(profile) > 0
        assert profile.isupper() or profile[0].isupper()
    
    def test_infer_style_profile_empty(self):
        """Empty purchases should return 'Unknown'."""
        analyzer = PreferenceAnalyzer()
        
        profile = analyzer.infer_style_profile([])
        
        assert profile == "Unknown"


class TestAnalyzerConfiguration:
    """Test analyzer configuration options."""
    
    def test_custom_top_n(self):
        """Custom top_n configuration."""
        analyzer_small = PreferenceAnalyzer(top_n=2)
        analyzer_large = PreferenceAnalyzer(top_n=10)
        
        titles = [
            "Blue Shirt", "Blue Pants",
            "Black Jacket", "Black Tie",
            "Red Dress", "Red Scarf"
        ]
        
        small_result = analyzer_small.analyze_preferences(titles)
        large_result = analyzer_large.analyze_preferences(titles)
        
        assert len(small_result["dominant_colors"]) <= 2
        assert len(large_result["dominant_colors"]) <= 3  # Only 3 unique colors
    
    def test_custom_min_frequency(self):
        """Custom minimum frequency configuration."""
        analyzer_strict = PreferenceAnalyzer(min_frequency=3)
        analyzer_lenient = PreferenceAnalyzer(min_frequency=1)
        
        titles = [
            "Blue Shirt", "Blue Pants", "Blue Shoes",
            "Black Jacket",
            "Red Dress"
        ]
        
        strict_colors = analyzer_strict.extract_colors(titles)
        lenient_colors = analyzer_lenient.extract_colors(titles)
        
        # Strict should only have "blue" (appears 3 times)
        assert len(strict_colors) == 1
        assert "blue" in strict_colors
        
        # Lenient should have all colors
        assert len(lenient_colors) == 3


class TestRealWorldScenarios:
    """Test with realistic user purchase data."""
    
    def test_fashion_enthusiast(self):
        """Analyze fashion-focused user purchases."""
        analyzer = PreferenceAnalyzer()
        purchases = [
            "Blue formal evening dress",
            "Black classic blazer",
            "White elegant blouse",
            "Blue casual jeans",
            "Black comfortable loafers",
            "Blue trendy cardigan"
        ]
        categories = [
            "apparel", "apparel", "apparel",
            "apparel", "footwear", "apparel"
        ]
        
        analysis = analyzer.analyze_preferences(purchases, categories)
        
        assert analysis["purchase_count"] == 6
        assert analysis["dominant_colors"]["blue"] >= 3
        assert "apparel" in analysis["most_frequent_categories"]
        
        # Also test style profile
        style_profile = analyzer.infer_style_profile(purchases)
        assert style_profile != "Unknown"
    
    def test_mixed_preferences(self):
        """Analyze user with diverse preferences."""
        analyzer = PreferenceAnalyzer()
        purchases = [
            "Casual blue jeans",
            "Formal red dress",
            "Athletic black shoes",
            "Boho white scarf",
            "Vintage gray cardigan"
        ]
        
        analysis = analyzer.analyze_preferences(purchases)
        
        assert len(analysis["dominant_colors"]) > 0
        assert len(analysis["style_keywords"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
