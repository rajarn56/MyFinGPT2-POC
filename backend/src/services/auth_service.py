from typing import Optional
from loguru import logger

from src.config import settings
from src.services.session_service import SessionService


class AuthService:
    def __init__(self):
        self.api_keys = set(settings.API_KEYS.split(","))
        self.session_service = SessionService()
    
    def validate_api_key(self, api_key: str) -> bool:
        """Validate API key"""
        return api_key in self.api_keys
    
    def create_session_from_api_key(self, api_key: str) -> Optional[str]:
        """Create session from API key"""
        if not self.validate_api_key(api_key):
            logger.warning(f"Invalid API key attempted")
            return None
        
        # For POC, use API key as user_id (in production, map to actual user)
        user_id = f"user_{api_key[:8]}"
        session = self.session_service.create_session(user_id)
        return session.session_id

