"""
Preference analyzer for inferring user style from past purchases.
Extracts dominant colors, frequent categories, and style keywords.
"""
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter
import re


# Common color names for matching in text
COMMON_COLORS = {
    'red', 'blue', 'green', 'yellow', 'orange', 'purple', 'pink', 'brown',
    'black', 'white', 'gray', 'grey', 'beige', 'navy', 'teal', 'gold',
    'silver', 'bronze', 'copper', 'maroon', 'burgundy', 'coral', 'turquoise',
    'khaki', 'olive', 'lime', 'cream', 'ivory', 'charcoal', 'indigo',
    'violet', 'aqua', 'cyan', 'magenta', 'peach', 'salmon', 'rust',
    'sage', 'emerald', 'forest', 'mint', 'chocolate'
}

# Style keywords that indicate fashion preferences
STYLE_KEYWORDS = {
    'formal', 'casual', 'business', 'athletic', 'sporty', 'vintage', 'modern',
    'classic', 'bohemian', 'boho', 'trendy', 'elegant', 'minimalist', 'chic',
    'cozy', 'comfortable', 'professional', 'streetwear', 'designer', 'luxury',
    'eco', 'sustainable', 'organic', 'handmade', 'vintage', 'retro', 'edgy',
    'preppy', 'hipster', 'gothic', 'romantic', 'floral', 'geometric', 'striped',
    'bold', 'subtle', 'statement', 'oversized', 'fitted', 'loose', 'slim',
    'distressed', 'weathered', 'premium', 'basic', 'essential'
}

# Product types/categories to look for in titles
PRODUCT_TYPES = {
    'shirt', 'dress', 'pants', 'jeans', 'shorts', 'skirt', 'blouse', 'jacket',
    'coat', 'sweater', 'hoodie', 'cardigan', 'vest', 'suit', 'blazer', 'shoe',
    'shoes', 'boot', 'boots', 'sneaker', 'sandal', 'heel', 'pump', 'loafer',
    'hat', 'cap', 'bag', 'purse', 'backpack', 'wallet', 'belt', 'scarf',
    'tie', 'socks', 'underwear', 'bra', 'leggings', 'tights', 'watch',
    'bracelet', 'necklace', 'earring', 'ring', 'sunglasses', 'glasses',
    'gloves', 'mittens', 'sweatpants', 'joggers', 'jumper', 'dress'
}


class PreferenceAnalyzer:
    """Analyzes user purchase history to infer style preferences."""
    
    def __init__(self, min_frequency: int = 1, top_n: int = 5):
        """
        Initialize preference analyzer.
        
        Args:
            min_frequency: Minimum frequency for items to be included in results
            top_n: Number of top results to return for each category
        """
        self.min_frequency = min_frequency
        self.top_n = top_n
    
    def extract_colors(self, titles: List[str]) -> Dict[str, int]:
        """
        Extract dominant colors from product titles.
        
        Args:
            titles: List of product titles
            
        Returns:
            Dictionary mapping color to frequency, sorted by frequency
        """
        color_freq: Dict[str, int] = {}
        
        for title in titles:
            if not title:
                continue
            
            # Convert to lowercase for matching
            title_lower = title.lower()
            
            # Extract color keywords
            for color in COMMON_COLORS:
                # Use word boundaries to avoid partial matches
                if re.search(r'\b' + re.escape(color) + r'\b', title_lower):
                    color_freq[color] = color_freq.get(color, 0) + 1
        
        # Filter by minimum frequency and sort
        filtered_colors = {
            k: v for k, v in sorted(
                color_freq.items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            if v >= self.min_frequency
        }
        
        return filtered_colors
    
    def extract_categories(self, categories: List[str]) -> Dict[str, int]:
        """
        Extract most frequent categories.
        
        Args:
            categories: List of category names
            
        Returns:
            Dictionary mapping category to frequency, sorted by frequency
        """
        if not categories:
            return {}
        
        # Normalize categories (lowercase)
        normalized = [cat.lower().strip() for cat in categories if cat]
        
        # Count frequencies
        category_freq = dict(Counter(normalized))
        
        # Filter by minimum frequency and sort
        filtered_categories = {
            k: v for k, v in sorted(
                category_freq.items(),
                key=lambda x: x[1],
                reverse=True
            )
            if v >= self.min_frequency
        }
        
        return filtered_categories
    
    def extract_style_keywords(self, titles: List[str]) -> Dict[str, int]:
        """
        Extract style-related keywords from product titles.
        
        Args:
            titles: List of product titles
            
        Returns:
            Dictionary mapping keyword to frequency, sorted by frequency
        """
        keyword_freq: Dict[str, int] = {}
        
        for title in titles:
            if not title:
                continue
            
            title_lower = title.lower()
            
            # Extract style keywords
            for keyword in STYLE_KEYWORDS:
                if re.search(r'\b' + re.escape(keyword) + r'\b', title_lower):
                    keyword_freq[keyword] = keyword_freq.get(keyword, 0) + 1
        
        # Filter by minimum frequency and sort
        filtered_keywords = {
            k: v for k, v in sorted(
                keyword_freq.items(),
                key=lambda x: x[1],
                reverse=True
            )
            if v >= self.min_frequency
        }
        
        return filtered_keywords
    
    def extract_product_types(self, titles: List[str]) -> Dict[str, int]:
        """
        Extract product types/categories from titles.
        
        Args:
            titles: List of product titles
            
        Returns:
            Dictionary mapping product type to frequency
        """
        type_freq: Dict[str, int] = {}
        
        for title in titles:
            if not title:
                continue
            
            title_lower = title.lower()
            
            # Extract product types
            for ptype in PRODUCT_TYPES:
                if re.search(r'\b' + re.escape(ptype) + r'\b', title_lower):
                    type_freq[ptype] = type_freq.get(ptype, 0) + 1
        
        # Filter by minimum frequency and sort
        filtered_types = {
            k: v for k, v in sorted(
                type_freq.items(),
                key=lambda x: x[1],
                reverse=True
            )
            if v >= self.min_frequency
        }
        
        return filtered_types
    
    def analyze_preferences(
        self,
        past_purchases: List[str],
        categories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze user preferences from purchase history.
        
        Args:
            past_purchases: List of purchased product titles
            categories: Optional list of corresponding categories
            
        Returns:
            Dictionary with analyzed preferences:
            {
                "dominant_colors": {color: frequency, ...},
                "most_frequent_categories": {category: frequency, ...},
                "style_keywords": {keyword: frequency, ...},
                "product_types": {type: frequency, ...},
                "purchase_count": int,
                "unique_colors": int,
                "unique_categories": int,
                "unique_keywords": int
            }
        """
        if not past_purchases:
            return {
                "dominant_colors": {},
                "most_frequent_categories": {},
                "style_keywords": {},
                "product_types": {},
                "purchase_count": 0,
                "unique_colors": 0,
                "unique_categories": 0,
                "unique_keywords": 0
            }
        
        # Extract colors from titles
        colors = self.extract_colors(past_purchases)
        
        # Extract categories (use provided or try to extract from titles)
        if categories and len(categories) == len(past_purchases):
            category_dict = self.extract_categories(categories)
        else:
            category_dict = {}
        
        # Extract style keywords
        keywords = self.extract_style_keywords(past_purchases)
        
        # Extract product types
        product_types = self.extract_product_types(past_purchases)
        
        # Limit top N results
        top_colors = dict(list(colors.items())[:self.top_n])
        top_categories = dict(list(category_dict.items())[:self.top_n])
        top_keywords = dict(list(keywords.items())[:self.top_n])
        top_types = dict(list(product_types.items())[:self.top_n])
        
        return {
            "dominant_colors": top_colors,
            "most_frequent_categories": top_categories,
            "style_keywords": top_keywords,
            "product_types": top_types,
            "purchase_count": len(past_purchases),
            "unique_colors": len(colors),
            "unique_categories": len(category_dict),
            "unique_keywords": len(keywords)
        }
    
    def get_top_colors(self, past_purchases: List[str], n: int = 3) -> List[str]:
        """
        Get top N dominant colors from purchase history.
        
        Args:
            past_purchases: List of product titles
            n: Number of colors to return
            
        Returns:
            List of top N colors
        """
        colors = self.extract_colors(past_purchases)
        return list(colors.keys())[:n]
    
    def get_top_categories(
        self,
        categories: List[str],
        n: int = 3
    ) -> List[str]:
        """
        Get top N most frequent categories.
        
        Args:
            categories: List of category names
            n: Number of categories to return
            
        Returns:
            List of top N categories
        """
        cat_dict = self.extract_categories(categories)
        return list(cat_dict.keys())[:n]
    
    def get_top_style_keywords(self, past_purchases: List[str], n: int = 5) -> List[str]:
        """
        Get top N style keywords from purchase history.
        
        Args:
            past_purchases: List of product titles
            n: Number of keywords to return
            
        Returns:
            List of top N keywords
        """
        keywords = self.extract_style_keywords(past_purchases)
        return list(keywords.keys())[:n]
    
    def infer_style_profile(
        self,
        past_purchases: List[str],
        categories: Optional[List[str]] = None
    ) -> str:
        """
        Infer overall style profile from keywords and purchases.
        
        Args:
            past_purchases: List of product titles
            categories: Optional list of categories
            
        Returns:
            Inferred style profile as a descriptive string
        """
        if not past_purchases:
            return "Unknown"
        
        analysis = self.analyze_preferences(past_purchases, categories)
        keywords = analysis.get("style_keywords", {})
        
        if not keywords:
            return "Undefined"
        
        # Get top keywords for profile description
        top_keywords = list(keywords.keys())[:3]
        
        # Map keywords to style profiles
        profile_keywords = ", ".join(top_keywords)
        return profile_keywords.title()
