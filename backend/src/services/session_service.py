import secrets
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from loguru import logger

from src.models.session import Session
from src.config import settings
from src.utils.paths import get_data_path


class SessionService:
    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize SessionService
        
        Args:
            storage_path: Optional custom storage path. If None, uses project root/data/sessions
        """
        if storage_path is None:
            storage_path = get_data_path("sessions")
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.timeout_hours = settings.SESSION_TIMEOUT_HOURS
    
    def create_session(self, user_id: str) -> Session:
        """Create a new session"""
        session_id = secrets.token_urlsafe(32)
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=self.timeout_hours)
        
        session = Session(
            session_id=session_id,
            user_id=user_id,
            created_at=now,
            expires_at=expires_at,
            last_activity=now
        )
        
        self._save_session(session)
        logger.info(f"Created session {session_id} for user {user_id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID"""
        session_file = self.storage_path / f"{session_id}.json"
        if not session_file.exists():
            return None
        
        try:
            with open(session_file, "r") as f:
                data = json.load(f)
            # Convert datetime strings back to datetime objects
            data["created_at"] = datetime.fromisoformat(data["created_at"])
            data["expires_at"] = datetime.fromisoformat(data["expires_at"])
            data["last_activity"] = datetime.fromisoformat(data["last_activity"])
            session = Session(**data)
            
            # Check expiration
            if session.expires_at < datetime.utcnow():
                self.delete_session(session_id)
                return None
            
            return session
        except Exception as e:
            logger.error(f"Error loading session {session_id}: {e}")
            return None
    
    def update_activity(self, session_id: str):
        """Update last activity timestamp"""
        session = self.get_session(session_id)
        if session:
            session.last_activity = datetime.utcnow()
            self._save_session(session)
    
    def delete_session(self, session_id: str):
        """Delete a session"""
        session_file = self.storage_path / f"{session_id}.json"
        if session_file.exists():
            session_file.unlink()
            logger.info(f"Deleted session {session_id}")
    
    def _save_session(self, session: Session):
        """Save session to file"""
        session_file = self.storage_path / f"{session.session_id}.json"
        with open(session_file, "w") as f:
            json.dump(session.model_dump(), f, default=str)

