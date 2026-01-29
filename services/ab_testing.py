"""
A/B Testing Module for OmniSearch.

Handles experiment assignment, variant management, and metrics logging.
Supports in-memory and Redis-based storage.
"""

from typing import Dict, Optional, Any, List
from dataclasses import dataclass, asdict, field
from datetime import datetime
import random
import json
import logging
from enum import Enum
import os

logger = logging.getLogger(__name__)


class ExperimentVariant(str, Enum):
    """Available experiment variants."""
    SEARCH_V1 = "search_v1"
    SEARCH_V2 = "search_v2"


@dataclass
class ExperimentAssignment:
    """User's experiment assignment."""
    user_id: str
    variant: ExperimentVariant
    assigned_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "user_id": self.user_id,
            "variant": self.variant.value,
            "assigned_at": self.assigned_at.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class ExperimentEvent:
    """Base event for experiment tracking."""
    user_id: str
    variant: ExperimentVariant
    timestamp: datetime = field(default_factory=datetime.utcnow)
    query: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "user_id": self.user_id,
            "variant": self.variant.value,
            "timestamp": self.timestamp.isoformat(),
            "query": self.query,
            "session_id": self.session_id,
            "metadata": self.metadata
        }


@dataclass
class SearchEvent(ExperimentEvent):
    """Search query event."""
    results_count: int = 0
    search_time_ms: float = 0.0
    event_type: str = "search"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        d = super().to_dict()
        d.update({
            "results_count": self.results_count,
            "search_time_ms": self.search_time_ms,
            "event_type": self.event_type
        })
        return d


@dataclass
class ClickEvent(ExperimentEvent):
    """Click/interaction event."""
    product_id: str = ""
    product_title: str = ""
    position: int = -1
    event_type: str = "click"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        d = super().to_dict()
        d.update({
            "product_id": self.product_id,
            "product_title": self.product_title,
            "position": self.position,
            "event_type": self.event_type
        })
        return d


class ExperimentManager:
    """Manages A/B test assignments and metrics."""
    
    def __init__(self, 
                 variants: List[ExperimentVariant] = None,
                 split_ratio: float = 0.5,
                 storage_backend: str = "memory"):
        """
        Initialize experiment manager.
        
        Args:
            variants: List of variants to test (default: SEARCH_V1, SEARCH_V2)
            split_ratio: Probability weight for first variant (0-1)
            storage_backend: "memory", "redis", or "file"
        """
        self.variants = variants or [ExperimentVariant.SEARCH_V1, ExperimentVariant.SEARCH_V2]
        self.split_ratio = split_ratio
        self.storage_backend = storage_backend
        
        # In-memory storage
        self._assignments: Dict[str, ExperimentAssignment] = {}
        self._events: List[ExperimentEvent] = []
        
        # Redis client (lazy initialized)
        self._redis = None
        
        # Event log file path
        self.log_file = os.getenv("AB_LOG_FILE", "ab_events.jsonl")
        
        if storage_backend == "redis":
            self._init_redis()
    
    def _init_redis(self):
        """Initialize Redis connection."""
        try:
            import redis
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            self._redis = redis.from_url(redis_url)
            self._redis.ping()
            logger.info(f"Redis connected for A/B testing: {redis_url}")
        except ImportError:
            logger.warning("redis package not installed. Falling back to memory storage.")
            self.storage_backend = "memory"
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Falling back to memory storage.")
            self.storage_backend = "memory"
    
    def assign_variant(self, 
                      user_id: str, 
                      metadata: Dict[str, Any] = None) -> ExperimentAssignment:
        """
        Assign a user to a variant.
        
        If already assigned, returns existing assignment.
        Uses split_ratio to determine variant probability.
        
        Args:
            user_id: Unique user identifier
            metadata: Additional metadata (session, device, etc.)
            
        Returns:
            ExperimentAssignment with user_id, variant, and timestamp
        """
        # Check existing assignment
        existing = self.get_assignment(user_id)
        if existing:
            return existing
        
        # Random assignment based on split_ratio
        variant = (
            self.variants[0] 
            if random.random() < self.split_ratio 
            else self.variants[1]
        )
        
        assignment = ExperimentAssignment(
            user_id=user_id,
            variant=variant,
            metadata=metadata or {}
        )
        
        # Store assignment
        self._store_assignment(assignment)
        
        logger.info(f"Assigned user {user_id} to {variant.value}")
        return assignment
    
    def get_assignment(self, user_id: str) -> Optional[ExperimentAssignment]:
        """
        Get existing assignment for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            ExperimentAssignment if exists, None otherwise
        """
        if self.storage_backend == "memory":
            return self._assignments.get(user_id)
        elif self.storage_backend == "redis":
            key = f"ab:assignment:{user_id}"
            data = self._redis.get(key)
            if data:
                d = json.loads(data)
                return ExperimentAssignment(
                    user_id=d["user_id"],
                    variant=ExperimentVariant(d["variant"]),
                    assigned_at=datetime.fromisoformat(d["assigned_at"]),
                    metadata=d.get("metadata", {})
                )
        return None
    
    def _store_assignment(self, assignment: ExperimentAssignment):
        """Store assignment in configured backend."""
        if self.storage_backend == "memory":
            self._assignments[assignment.user_id] = assignment
        elif self.storage_backend == "redis":
            key = f"ab:assignment:{assignment.user_id}"
            self._redis.set(
                key,
                json.dumps(assignment.to_dict()),
                ex=86400 * 30  # 30 days expiry
            )
    
    def log_event(self, event: ExperimentEvent):
        """
        Log an experiment event (search, click, etc.).
        
        Args:
            event: ExperimentEvent instance
        """
        # In-memory log
        self._events.append(event)
        
        # File log (JSONL)
        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(event.to_dict()) + "\n")
        except Exception as e:
            logger.error(f"Failed to write event log: {e}")
        
        # Redis log
        if self.storage_backend == "redis":
            key = f"ab:events:{event.user_id}"
            self._redis.lpush(key, json.dumps(event.to_dict()))
            self._redis.expire(key, 86400 * 30)  # 30 days
    
    def log_search(self, 
                  user_id: str,
                  query: str,
                  results_count: int,
                  search_time_ms: float = 0.0,
                  session_id: str = None) -> SearchEvent:
        """
        Log a search query event.
        
        Args:
            user_id: User performing search
            query: Search query string
            results_count: Number of results returned
            search_time_ms: Search execution time in milliseconds
            session_id: Session identifier
            
        Returns:
            SearchEvent that was logged
        """
        assignment = self.get_assignment(user_id) or self.assign_variant(user_id)
        
        event = SearchEvent(
            user_id=user_id,
            variant=assignment.variant,
            query=query,
            results_count=results_count,
            search_time_ms=search_time_ms,
            session_id=session_id
        )
        
        self.log_event(event)
        return event
    
    def log_click(self,
                 user_id: str,
                 product_id: str,
                 product_title: str = "",
                 position: int = -1,
                 query: str = None,
                 session_id: str = None) -> ClickEvent:
        """
        Log a click/interaction event.
        
        Args:
            user_id: User performing click
            product_id: Product clicked
            product_title: Product title (optional)
            position: Position in results (0-indexed, -1 if unknown)
            query: Original search query
            session_id: Session identifier
            
        Returns:
            ClickEvent that was logged
        """
        assignment = self.get_assignment(user_id) or self.assign_variant(user_id)
        
        event = ClickEvent(
            user_id=user_id,
            variant=assignment.variant,
            product_id=product_id,
            product_title=product_title,
            position=position,
            query=query,
            session_id=session_id
        )
        
        self.log_event(event)
        return event
    
    def get_events(self, 
                  user_id: str = None,
                  variant: ExperimentVariant = None,
                  event_type: str = None,
                  limit: int = 100) -> List[ExperimentEvent]:
        """
        Get events from in-memory storage.
        
        Args:
            user_id: Filter by user (optional)
            variant: Filter by variant (optional)
            event_type: Filter by event type: "search", "click" (optional)
            limit: Maximum events to return
            
        Returns:
            List of matching events
        """
        events = self._events
        
        if user_id:
            events = [e for e in events if e.user_id == user_id]
        if variant:
            events = [e for e in events if e.variant == variant]
        if event_type:
            events = [e for e in events if getattr(e, 'event_type', None) == event_type]
        
        return events[-limit:]  # Last N events
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get aggregate metrics from in-memory logs.
        
        Returns:
            Dict with total events, variant counts, search/click stats
        """
        search_events = [e for e in self._events if isinstance(e, SearchEvent)]
        click_events = [e for e in self._events if isinstance(e, ClickEvent)]
        
        v1_searches = sum(1 for e in search_events if e.variant == ExperimentVariant.SEARCH_V1)
        v2_searches = sum(1 for e in search_events if e.variant == ExperimentVariant.SEARCH_V2)
        
        v1_clicks = sum(1 for e in click_events if e.variant == ExperimentVariant.SEARCH_V1)
        v2_clicks = sum(1 for e in click_events if e.variant == ExperimentVariant.SEARCH_V2)
        
        return {
            "total_events": len(self._events),
            "total_assignments": len(self._assignments),
            "search_events": len(search_events),
            "click_events": len(click_events),
            "search_v1": {
                "count": v1_searches,
                "clicks": v1_clicks,
                "ctr": v1_clicks / v1_searches if v1_searches > 0 else 0
            },
            "search_v2": {
                "count": v2_searches,
                "clicks": v2_clicks,
                "ctr": v2_clicks / v2_searches if v2_searches > 0 else 0
            },
            "avg_search_time_ms": (
                sum(e.search_time_ms for e in search_events) / len(search_events)
                if search_events else 0
            ),
            "avg_results": (
                sum(e.results_count for e in search_events) / len(search_events)
                if search_events else 0
            )
        }
    
    def reset(self):
        """Clear all in-memory data (useful for testing)."""
        self._assignments.clear()
        self._events.clear()
        logger.info("A/B testing data cleared")


# Global instance
_experiment_manager: Optional[ExperimentManager] = None


def get_experiment_manager() -> ExperimentManager:
    """Get or create the global experiment manager instance."""
    global _experiment_manager
    if _experiment_manager is None:
        storage_backend = os.getenv("AB_STORAGE", "memory")
        split_ratio = float(os.getenv("AB_SPLIT_RATIO", "0.5"))
        _experiment_manager = ExperimentManager(
            storage_backend=storage_backend,
            split_ratio=split_ratio
        )
    return _experiment_manager


def reset_experiment_manager():
    """Reset the global instance (useful for testing)."""
    global _experiment_manager
    _experiment_manager = None
