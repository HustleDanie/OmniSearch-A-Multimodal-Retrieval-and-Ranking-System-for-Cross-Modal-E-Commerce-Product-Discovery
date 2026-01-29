"""
Click tracking and metrics logging module for search results.

Records:
- Clicks on search results
- Result rank/position of clicks
- Click-through rates (CTR)
- Response times
- Stores metrics in MongoDB for analysis
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict, field
from enum import Enum
import os


# MongoDB setup
try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False


class ClickSource(str, Enum):
    """Source of the click event."""
    SEARCH_RESULTS = "search_results"
    RECOMMENDATIONS = "recommendations"
    FEATURED = "featured"
    OTHER = "other"


@dataclass
class ClickEvent:
    """Click event data."""
    user_id: str
    product_id: str
    rank: int  # Position clicked (0-based)
    search_query: str
    variant: str  # "search_v1" or "search_v2"
    response_time_ms: float
    session_id: Optional[str] = None
    source: str = ClickSource.SEARCH_RESULTS.value
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        data = asdict(self)
        data['timestamp'] = self.timestamp
        return data


@dataclass
class SearchImpression:
    """Search impression (query executed)."""
    user_id: str
    query: str
    variant: str  # "search_v1" or "search_v2"
    results_count: int
    response_time_ms: float
    session_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        data = asdict(self)
        data['timestamp'] = self.timestamp
        return data


class ClickTrackingService:
    """Service for tracking clicks and calculating metrics."""
    
    def __init__(self, mongodb_uri: Optional[str] = None):
        """
        Initialize click tracking service.
        
        Args:
            mongodb_uri: MongoDB connection URI
                        (defaults to MONGODB_URI env var or localhost)
        """
        self.mongodb_uri = mongodb_uri or os.getenv(
            'MONGODB_URI',
            'mongodb://localhost:27017'
        )
        self.db = None
        self.clicks_collection = None
        self.impressions_collection = None
        self._initialize_mongodb()
    
    def _initialize_mongodb(self):
        """Initialize MongoDB connection and collections."""
        if not MONGODB_AVAILABLE:
            print("Warning: pymongo not available. Click tracking disabled.")
            return
        
        try:
            client = MongoClient(
                self.mongodb_uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000
            )
            # Verify connection
            client.admin.command('ping')
            self.db = client['omnisearch']
            self.clicks_collection = self.db['clicks']
            self.impressions_collection = self.db['impressions']
            
            # Create indexes for common queries
            self._create_indexes()
            
        except (ConnectionFailure, ServerSelectionTimeoutError):
            print(f"Warning: Could not connect to MongoDB at {self.mongodb_uri}")
            self.db = None
    
    def _create_indexes(self):
        """Create indexes for efficient querying."""
        if not self.db:
            return
        
        # Clicks indexes
        self.clicks_collection.create_index('user_id')
        self.clicks_collection.create_index('variant')
        self.clicks_collection.create_index('timestamp')
        self.clicks_collection.create_index([('user_id', 1), ('timestamp', -1)])
        self.clicks_collection.create_index([('variant', 1), ('timestamp', -1)])
        
        # Impressions indexes
        self.impressions_collection.create_index('user_id')
        self.impressions_collection.create_index('variant')
        self.impressions_collection.create_index('timestamp')
        self.impressions_collection.create_index([('user_id', 1), ('timestamp', -1)])
        self.impressions_collection.create_index([('variant', 1), ('timestamp', -1)])
    
    def log_click(self, click_event: ClickEvent) -> bool:
        """
        Log a click event.
        
        Args:
            click_event: ClickEvent object with click data
            
        Returns:
            True if logged successfully, False otherwise
        """
        if not self.db:
            return False
        
        try:
            result = self.clicks_collection.insert_one(click_event.to_dict())
            return result.acknowledged
        except Exception as e:
            print(f"Error logging click: {str(e)}")
            return False
    
    def log_impression(self, impression: SearchImpression) -> bool:
        """
        Log a search impression (query executed).
        
        Args:
            impression: SearchImpression object
            
        Returns:
            True if logged successfully, False otherwise
        """
        if not self.db:
            return False
        
        try:
            result = self.impressions_collection.insert_one(impression.to_dict())
            return result.acknowledged
        except Exception as e:
            print(f"Error logging impression: {str(e)}")
            return False
    
    def get_ctr(self,
                user_id: Optional[str] = None,
                variant: Optional[str] = None,
                days: int = 7) -> Dict[str, float]:
        """
        Calculate click-through rate.
        
        Args:
            user_id: Filter by user (optional)
            variant: Filter by variant "search_v1" or "search_v2" (optional)
            days: Look back period in days (default 7)
            
        Returns:
            Dict with overall CTR and breakdown by variant
        """
        if not self.db:
            return {"ctr": 0.0, "clicks": 0, "impressions": 0}
        
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        
        # Build filters
        click_filter = {'timestamp': {'$gte': cutoff_time}}
        impression_filter = {'timestamp': {'$gte': cutoff_time}}
        
        if user_id:
            click_filter['user_id'] = user_id
            impression_filter['user_id'] = user_id
        
        if variant:
            click_filter['variant'] = variant
            impression_filter['variant'] = variant
        
        try:
            # Count clicks and impressions
            clicks = self.clicks_collection.count_documents(click_filter)
            impressions = self.impressions_collection.count_documents(impression_filter)
            
            ctr = clicks / impressions if impressions > 0 else 0.0
            
            result = {
                "ctr": round(ctr, 4),
                "clicks": clicks,
                "impressions": impressions,
                "period_days": days
            }
            
            # Add per-variant breakdown if not filtering by variant
            if not variant:
                for v in ["search_v1", "search_v2"]:
                    variant_clicks = self.clicks_collection.count_documents(
                        {**click_filter, 'variant': v}
                    )
                    variant_impressions = self.impressions_collection.count_documents(
                        {**impression_filter, 'variant': v}
                    )
                    variant_ctr = variant_clicks / variant_impressions if variant_impressions > 0 else 0.0
                    
                    result[f"ctr_{v}"] = round(variant_ctr, 4)
                    result[f"clicks_{v}"] = variant_clicks
                    result[f"impressions_{v}"] = variant_impressions
            
            return result
            
        except Exception as e:
            print(f"Error calculating CTR: {str(e)}")
            return {"ctr": 0.0, "clicks": 0, "impressions": 0}
    
    def get_rank_metrics(self,
                         user_id: Optional[str] = None,
                         variant: Optional[str] = None,
                         days: int = 7) -> Dict[str, Any]:
        """
        Get metrics about which result ranks get clicked.
        
        Args:
            user_id: Filter by user (optional)
            variant: Filter by variant (optional)
            days: Look back period in days
            
        Returns:
            Dict with rank statistics
        """
        if not self.db:
            return {"avg_rank": 0, "clicks_by_rank": {}}
        
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        
        # Build filter
        filter_dict = {'timestamp': {'$gte': cutoff_time}}
        if user_id:
            filter_dict['user_id'] = user_id
        if variant:
            filter_dict['variant'] = variant
        
        try:
            clicks = list(self.clicks_collection.find(filter_dict))
            
            if not clicks:
                return {
                    "avg_rank": 0,
                    "clicks_by_rank": {},
                    "total_clicks": 0
                }
            
            # Calculate statistics
            ranks = [click['rank'] for click in clicks]
            avg_rank = sum(ranks) / len(ranks)
            
            # Count clicks by rank
            clicks_by_rank = {}
            for click in clicks:
                rank = click['rank']
                clicks_by_rank[rank] = clicks_by_rank.get(rank, 0) + 1
            
            return {
                "avg_rank": round(avg_rank, 2),
                "median_rank": sorted(ranks)[len(ranks) // 2],
                "min_rank": min(ranks),
                "max_rank": max(ranks),
                "clicks_by_rank": dict(sorted(clicks_by_rank.items())),
                "total_clicks": len(clicks)
            }
            
        except Exception as e:
            print(f"Error calculating rank metrics: {str(e)}")
            return {"avg_rank": 0, "clicks_by_rank": {}, "total_clicks": 0}
    
    def get_response_time_metrics(self,
                                  user_id: Optional[str] = None,
                                  variant: Optional[str] = None,
                                  days: int = 7) -> Dict[str, float]:
        """
        Get response time statistics.
        
        Args:
            user_id: Filter by user (optional)
            variant: Filter by variant (optional)
            days: Look back period in days
            
        Returns:
            Dict with response time statistics
        """
        if not self.db:
            return {"avg_response_time_ms": 0, "count": 0}
        
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        
        # Build filter
        filter_dict = {'timestamp': {'$gte': cutoff_time}}
        if user_id:
            filter_dict['user_id'] = user_id
        if variant:
            filter_dict['variant'] = variant
        
        try:
            impressions = list(self.impressions_collection.find(filter_dict))
            
            if not impressions:
                return {
                    "avg_response_time_ms": 0,
                    "min_response_time_ms": 0,
                    "max_response_time_ms": 0,
                    "count": 0
                }
            
            times = [imp['response_time_ms'] for imp in impressions]
            avg_time = sum(times) / len(times)
            
            return {
                "avg_response_time_ms": round(avg_time, 2),
                "min_response_time_ms": round(min(times), 2),
                "max_response_time_ms": round(max(times), 2),
                "p95_response_time_ms": round(sorted(times)[int(len(times) * 0.95)], 2),
                "count": len(times)
            }
            
        except Exception as e:
            print(f"Error calculating response time metrics: {str(e)}")
            return {"avg_response_time_ms": 0, "count": 0}
    
    def get_user_summary(self, user_id: str, days: int = 7) -> Dict[str, Any]:
        """
        Get comprehensive summary for a user.
        
        Args:
            user_id: User ID
            days: Look back period in days
            
        Returns:
            Dict with all metrics for user
        """
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        filter_dict = {'user_id': user_id, 'timestamp': {'$gte': cutoff_time}}
        
        if not self.db:
            return {"user_id": user_id, "error": "Database unavailable"}
        
        try:
            clicks = list(self.clicks_collection.find(filter_dict))
            impressions = list(self.impressions_collection.find(filter_dict))
            
            return {
                "user_id": user_id,
                "period_days": days,
                "total_clicks": len(clicks),
                "total_impressions": len(impressions),
                "ctr": round(len(clicks) / len(impressions), 4) if impressions else 0.0,
                "avg_rank_clicked": round(
                    sum(c['rank'] for c in clicks) / len(clicks), 2
                ) if clicks else 0.0,
                "avg_response_time_ms": round(
                    sum(i['response_time_ms'] for i in impressions) / len(impressions), 2
                ) if impressions else 0.0,
                "variants_used": list(set([imp['variant'] for imp in impressions]))
            }
        except Exception as e:
            print(f"Error getting user summary: {str(e)}")
            return {"user_id": user_id, "error": str(e)}
    
    def get_variant_comparison(self, days: int = 7) -> Dict[str, Any]:
        """
        Get comparative metrics between variants.
        
        Args:
            days: Look back period in days
            
        Returns:
            Dict comparing search_v1 and search_v2
        """
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        filter_dict = {'timestamp': {'$gte': cutoff_time}}
        
        if not self.db:
            return {"error": "Database unavailable"}
        
        try:
            results = {}
            
            for variant in ["search_v1", "search_v2"]:
                v_filter = {**filter_dict, 'variant': variant}
                
                clicks = self.clicks_collection.count_documents(v_filter)
                impressions = self.impressions_collection.count_documents(v_filter)
                
                # Get response times
                imps = list(self.impressions_collection.find(
                    {**filter_dict, 'variant': variant},
                    {'response_time_ms': 1}
                ))
                
                response_times = [imp.get('response_time_ms', 0) for imp in imps]
                avg_response_time = sum(response_times) / len(response_times) if response_times else 0
                
                # Get rank metrics
                cls = list(self.clicks_collection.find(
                    v_filter,
                    {'rank': 1}
                ))
                ranks = [c.get('rank', 0) for c in cls]
                avg_rank = sum(ranks) / len(ranks) if ranks else 0
                
                results[variant] = {
                    "clicks": clicks,
                    "impressions": impressions,
                    "ctr": round(clicks / impressions, 4) if impressions else 0.0,
                    "avg_rank_clicked": round(avg_rank, 2),
                    "avg_response_time_ms": round(avg_response_time, 2)
                }
            
            return {
                "period_days": days,
                "variants": results,
                "winner_by_ctr": max(results.items(), key=lambda x: x[1]['ctr'])[0]
            }
            
        except Exception as e:
            print(f"Error comparing variants: {str(e)}")
            return {"error": str(e)}
    
    def reset(self) -> bool:
        """Delete all tracked data (careful!)."""
        if not self.db:
            return False
        
        try:
            self.clicks_collection.delete_many({})
            self.impressions_collection.delete_many({})
            return True
        except Exception as e:
            print(f"Error resetting: {str(e)}")
            return False


# Global singleton
_click_tracker = None


def get_click_tracker(mongodb_uri: Optional[str] = None) -> ClickTrackingService:
    """Get or create global click tracking service."""
    global _click_tracker
    if _click_tracker is None:
        _click_tracker = ClickTrackingService(mongodb_uri)
    return _click_tracker


def reset_click_tracker():
    """Reset global click tracker (for testing)."""
    global _click_tracker
    _click_tracker = None
