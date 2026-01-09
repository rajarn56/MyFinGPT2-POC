from fastapi import APIRouter, Header, HTTPException, Depends

from src.services.auth_service import AuthService
from src.services.session_service import SessionService

router = APIRouter()


def get_auth_service() -> AuthService:
    return AuthService()


def get_session_service() -> SessionService:
    return SessionService()


@router.post("/session")
async def create_session(
    x_api_key: str = Header(..., alias="X-API-Key"),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Create a session from API key"""
    session_id = auth_service.create_session_from_api_key(x_api_key)
    if not session_id:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    session = auth_service.session_service.get_session(session_id)
    return {
        "session_id": session_id,
        "expires_at": session.expires_at.isoformat()
    }


@router.get("/status")
async def get_status(
    x_session_id: str = Header(..., alias="X-Session-ID"),
    session_service: SessionService = Depends(get_session_service)
):
    """Get session status"""
    session = session_service.get_session(x_session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    session_service.update_activity(x_session_id)
    
    return {
        "status": "ok",
        "session": {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "expires_at": session.expires_at.isoformat()
        }
    }

