"""
Context retrieval service for LLM input generation.
Retrieves user preferences and search results in structured format for LLM consumption.
"""
from typing import List, Dict, Any, Optional
import importlib.util
from pathlib import Path


class ContextRetriever:
    """Retrieves and formats user context and search results for LLM input."""
    
    def __init__(self):
        """Initialize context retriever with services."""
        # Lazy load services to avoid import issues in tests
        self.preference_analyzer = self._load_preference_analyzer()
        self.user_service = self._load_user_service()
    
    @staticmethod
    def _load_preference_analyzer():
        """Load PreferenceAnalyzer directly."""
        spec = importlib.util.spec_from_file_location(
            "preference_analyzer",
            Path(__file__).parent / "preference_analyzer.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.PreferenceAnalyzer(top_n=5, min_frequency=1)
    
    @staticmethod
    def _load_user_service():
        """Load UserProfileService directly."""
        spec = importlib.util.spec_from_file_location(
            "user_service",
            Path(__file__).parent.parent / "db" / "user_service.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.UserProfileService()
    
    def retrieve_context(
        self,
        user_id: str,
        search_results: List[Dict[str, Any]],
        max_results: int = 5
    ) -> str:
        """
        Retrieve user preferences and search results formatted for LLM input.
        
        Args:
            user_id: MongoDB user ID
            search_results: List of search result dicts with keys:
                - title (str)
                - description (str, optional)
                - color (str, optional)
                - category (str, optional)
                - score (float, optional)
                - _id (str, optional)
            max_results: Maximum number of search results to include (default: 5)
        
        Returns:
            Structured text formatted for LLM input containing:
            - User preferences summary
            - Top search results with details
            
        Example Output:
            ```
            USER PREFERENCES:
            - Preferred Colors: blue (3), black (2), white (1)
            - Favorite Categories: apparel (8), footwear (3)
            - Style Profile: Classic elegant style with casual comfort elements
            - Popular Styles: casual, elegant, comfortable, classic
            - Preferred Types: shirt, dress, shoes, pants
            
            SEARCH RESULTS (5 items):
            
            Result 1: Blue Casual Cotton Shirt
            Description: Comfortable everyday shirt made from 100% cotton
            Category: apparel
            Color: blue
            Relevance Score: 0.92
            
            Result 2: Black Elegant Blazer
            Description: Professional blazer perfect for formal occasions
            Category: apparel
            Color: black
            Relevance Score: 0.88
            
            [...]
            ```
        """
        # Fetch user profile and preferences
        user_profile = self.user_service.get_user_profile(user_id)
        
        if not user_profile:
            return self._format_empty_context(search_results, max_results)
        
        # Analyze user preferences from purchase history
        past_purchases = user_profile.get("past_purchases", [])
        past_categories = user_profile.get("purchase_categories", [])
        
        preferences_analysis = self.preference_analyzer.analyze_preferences(
            past_purchases, past_categories
        )
        
        # Build user preferences summary
        preferences_summary = self._build_preferences_summary(
            user_profile, preferences_analysis
        )
        
        # Format search results
        results_summary = self._format_search_results(search_results, max_results)
        
        # Combine into structured context for LLM
        context = f"""USER PREFERENCES:
{preferences_summary}

SEARCH RESULTS ({min(len(search_results), max_results)} items):
{results_summary}"""
        
        return context
    
    def _build_preferences_summary(
        self,
        user_profile: Dict[str, Any],
        preferences_analysis: Dict[str, Any]
    ) -> str:
        """Build formatted user preferences summary."""
        lines = []
        
        # Dominant colors
        colors = preferences_analysis.get("dominant_colors", {})
        if colors:
            color_str = ", ".join(
                f"{color} ({freq})"
                for color, freq in list(colors.items())[:5]
            )
            lines.append(f"- Preferred Colors: {color_str}")
        
        # Most frequent categories
        categories = preferences_analysis.get("most_frequent_categories", {})
        if categories:
            cat_str = ", ".join(
                f"{cat} ({freq})"
                for cat, freq in list(categories.items())[:5]
            )
            lines.append(f"- Favorite Categories: {cat_str}")
        
        # Style profile
        style_profile = self.preference_analyzer.infer_style_profile(
            user_profile.get("past_purchases", [])
        )
        if style_profile != "Unknown":
            lines.append(f"- Style Profile: {style_profile}")
        
        # Popular style keywords
        keywords = preferences_analysis.get("style_keywords", {})
        if keywords:
            keyword_str = ", ".join(
                f"{kw}"
                for kw in list(keywords.keys())[:5]
            )
            lines.append(f"- Popular Styles: {keyword_str}")
        
        # Preferred product types
        product_types = preferences_analysis.get("product_types", {})
        if product_types:
            type_str = ", ".join(
                f"{ptype}"
                for ptype in list(product_types.keys())[:5]
            )
            lines.append(f"- Preferred Types: {type_str}")
        
        # Purchase history stats
        purchase_count = preferences_analysis.get("purchase_count", 0)
        if purchase_count > 0:
            lines.append(f"- Total Purchases Analyzed: {purchase_count}")
        
        # User preferences from profile
        if "preferences" in user_profile:
            prefs = user_profile["preferences"]
            if prefs.get("price_range"):
                lines.append(f"- Price Range: {prefs['price_range']}")
            if prefs.get("size_preference"):
                lines.append(f"- Size Preference: {prefs['size_preference']}")
        
        return "\n".join(lines) if lines else "- No preference data available"
    
    def _format_search_results(
        self,
        search_results: List[Dict[str, Any]],
        max_results: int = 5
    ) -> str:
        """Format search results for LLM consumption."""
        if not search_results:
            return "No search results available."
        
        formatted_results = []
        
        for i, result in enumerate(search_results[:max_results], 1):
            result_text = f"\nResult {i}: {result.get('title', 'Untitled')}"
            
            if result.get("description"):
                result_text += f"\nDescription: {result['description']}"
            
            if result.get("category"):
                result_text += f"\nCategory: {result['category']}"
            
            if result.get("color"):
                result_text += f"\nColor: {result['color']}"
            
            if result.get("price"):
                result_text += f"\nPrice: ${result['price']}"
            
            if result.get("score") is not None:
                score = result['score']
                result_text += f"\nRelevance Score: {score:.2f}"
            
            # Add any additional relevant fields
            if result.get("size"):
                result_text += f"\nSize: {result['size']}"
            
            if result.get("brand"):
                result_text += f"\nBrand: {result['brand']}"
            
            formatted_results.append(result_text)
        
        return "\n".join(formatted_results)
    
    def _format_empty_context(
        self,
        search_results: List[Dict[str, Any]],
        max_results: int = 5
    ) -> str:
        """Format context when user profile not found."""
        results_summary = self._format_search_results(search_results, max_results)
        
        context = f"""USER PREFERENCES:
- No user profile found. Showing general search results.

SEARCH RESULTS ({min(len(search_results), max_results)} items):
{results_summary}"""
        
        return context


def retrieve_context(
    user_id: str,
    search_results: List[Dict[str, Any]],
    max_results: int = 5
) -> str:
    """
    Convenience function to retrieve user context and search results.
    
    Args:
        user_id: MongoDB user ID
        search_results: List of search result dicts
        max_results: Maximum search results to include (default: 5)
    
    Returns:
        Structured text formatted for LLM input
    
    Example:
        ```python
        context = retrieve_context(
            user_id="user_123",
            search_results=[
                {
                    "title": "Blue Casual Shirt",
                    "description": "Comfortable everyday shirt",
                    "color": "blue",
                    "category": "apparel",
                    "score": 0.92
                },
                # ... more results
            ]
        )
        
        # Use context in LLM prompt
        prompt = f"Based on this user context, recommend products:\n{context}"
        response = llm.generate(prompt)
        ```
    """
    retriever = ContextRetriever()
    return retriever.retrieve_context(user_id, search_results, max_results)
