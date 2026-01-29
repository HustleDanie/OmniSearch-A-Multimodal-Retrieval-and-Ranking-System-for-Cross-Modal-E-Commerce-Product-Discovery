"""
Middleware for A/B testing experiment assignment.

Injects experiment variant into request scope for use in endpoints.
"""

from fastapi import Request, Depends
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from starlette.responses import Response
from typing import Callable, Optional
import uuid
import logging

from services.ab_testing import get_experiment_manager, ExperimentVariant

logger = logging.getLogger(__name__)


class ABTestingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to assign and inject A/B test variant.
    
    Adds to request.state:
    - user_id: Extracted from header or generated
    - variant: Assigned experiment variant
    - session_id: Session identifier
    """
    
    def __init__(self, 
                 app: ASGIApp,
                 user_id_header: str = "X-User-ID",
                 session_id_header: str = "X-Session-ID"):
        """
        Initialize middleware.
        
        Args:
            app: FastAPI app
            user_id_header: Header name for user ID (default: X-User-ID)
            session_id_header: Header name for session ID (default: X-Session-ID)
        """
        super().__init__(app)
        self.user_id_header = user_id_header
        self.session_id_header = session_id_header
        self.manager = get_experiment_manager()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and inject A/B variant.
        
        Args:
            request: Incoming request
            call_next: Next middleware/endpoint
            
        Returns:
            Response
        """
        # Extract or generate user ID
        user_id = self._extract_user_id(request)
        
        # Extract or generate session ID
        session_id = self._extract_session_id(request)
        
        # Assign variant (or get existing)
        assignment = self.manager.assign_variant(user_id)
        
        # Inject into request state
        request.state.user_id = user_id
        request.state.variant = assignment.variant
        request.state.session_id = session_id
        request.state.ab_assignment = assignment
        
        # Add custom headers to response for tracking
        response = await call_next(request)
        response.headers["X-Variant"] = assignment.variant.value
        response.headers["X-User-ID"] = user_id
        response.headers["X-Session-ID"] = session_id
        
        return response
    
    def _extract_user_id(self, request: Request) -> str:
        """
        Extract user ID from request.
        
        Priority:
        1. Header (X-User-ID)
        2. Cookie (user_id)
        3. Generate new UUID
        
        Args:
            request: Request object
            
        Returns:
            User ID string
        """
        # From header
        if self.user_id_header in request.headers:
            return request.headers[self.user_id_header]
        
        # From cookie
        if "user_id" in request.cookies:
            return request.cookies["user_id"]
        
        # Generate new
        user_id = str(uuid.uuid4())
        logger.debug(f"Generated new user_id: {user_id}")
        return user_id
    
    def _extract_session_id(self, request: Request) -> str:
        """
        Extract session ID from request.
        
        Priority:
        1. Header (X-Session-ID)
        2. Cookie (session_id)
        3. Generate new UUID
        
        Args:
            request: Request object
            
        Returns:
            Session ID string
        """
        # From header
        if self.session_id_header in request.headers:
            return request.headers[self.session_id_header]
        
        # From cookie
        if "session_id" in request.cookies:
            return request.cookies["session_id"]
        
        # Generate new
        session_id = str(uuid.uuid4())
        logger.debug(f"Generated new session_id: {session_id}")
        return session_id


def inject_variant(request: Request) -> str:
    """
    Dependency to inject variant into endpoints.
    
    Usage:
        @app.get("/search")
        async def search(variant: str = Depends(inject_variant)):
            # variant is "search_v1" or "search_v2"
            pass
    
    Args:
        request: Request object (injected by FastAPI)
        
    Returns:
        Variant string
    """
    return getattr(request.state, 'variant', ExperimentVariant.SEARCH_V1).value


def get_user_id(request: Request) -> str:
    """
    Dependency to get user ID from request state.
    
    Args:
        request: Request object
        
    Returns:
        User ID string
    """
    return getattr(request.state, 'user_id', 'anonymous')


def get_session_id(request: Request) -> str:
    """
    Dependency to get session ID from request state.
    
    Args:
        request: Request object
        
    Returns:
        Session ID string
    """
    return getattr(request.state, 'session_id', '')
