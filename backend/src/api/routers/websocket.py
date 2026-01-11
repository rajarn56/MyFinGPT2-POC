"""WebSocket endpoints for real-time progress updates (Phase 7)"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

from src.services.progress_manager import progress_manager

router = APIRouter()


@router.websocket("/ws/progress/{session_id}")
async def websocket_progress(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for progress updates
    
    Args:
        websocket: WebSocket connection
        session_id: Session ID from path parameter
    """
    await progress_manager.connect(websocket, session_id)
    
    try:
        # Keep connection alive and handle incoming messages (if any)
        while True:
            try:
                # Wait for any message (client can send ping/pong)
                data = await websocket.receive_text()
                logger.debug(f"Received WebSocket message from session {session_id}: {data}")
                # Echo back or handle ping/pong if needed
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for session {session_id}")
                break
    except Exception as e:
        logger.error(f"Error in WebSocket handler for session {session_id}: {e}")
    finally:
        await progress_manager.disconnect(websocket, session_id)
