"""Progress tracking and WebSocket management service for Phase 7"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import WebSocket
from loguru import logger
import asyncio
import json


class ProgressEvent:
    """Progress event model"""
    
    def __init__(
        self,
        agent: str,
        event_type: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.timestamp = datetime.utcnow().isoformat() + "Z"
        self.agent = agent
        self.event_type = event_type
        self.message = message
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "timestamp": self.timestamp,
            "agent": self.agent,
            "event_type": self.event_type,
            "message": self.message,
            "metadata": self.metadata
        }


class ExecutionOrderEntry:
    """Execution order entry model"""
    
    def __init__(self, agent: str, start_time: datetime):
        self.agent = agent
        self.start_time = start_time
        self.end_time: Optional[datetime] = None
        self.status: str = "running"
    
    def complete(self):
        """Mark as completed"""
        self.end_time = datetime.utcnow()
        self.status = "completed"
    
    def fail(self):
        """Mark as failed"""
        self.end_time = datetime.utcnow()
        self.status = "failed"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "agent": self.agent,
            "start_time": self.start_time.isoformat() + "Z",
            "end_time": self.end_time.isoformat() + "Z" if self.end_time else None,
            "status": self.status
        }


class ProgressUpdate:
    """Progress update model"""
    
    def __init__(
        self,
        session_id: str,
        transaction_id: str,
        current_agent: Optional[str] = None,
        current_tasks: Optional[Dict[str, List[str]]] = None,
        progress_events: Optional[List[ProgressEvent]] = None,
        execution_order: Optional[List[ExecutionOrderEntry]] = None
    ):
        self.type = "progress_update"
        self.session_id = session_id
        self.transaction_id = transaction_id
        self.current_agent = current_agent
        self.current_tasks = current_tasks or {}
        self.progress_events = progress_events or []
        self.execution_order = execution_order or []
        self.timestamp = datetime.utcnow().isoformat() + "Z"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "type": self.type,
            "session_id": self.session_id,
            "transaction_id": self.transaction_id,
            "current_agent": self.current_agent,
            "current_tasks": self.current_tasks,
            "progress_events": [event.to_dict() for event in self.progress_events],
            "execution_order": [entry.to_dict() for entry in self.execution_order],
            "timestamp": self.timestamp
        }


class ProgressManager:
    """Manages progress tracking and WebSocket connections"""
    
    def __init__(self):
        """Initialize progress manager"""
        # Map session_id -> List[WebSocket]
        self._connections: Dict[str, List[WebSocket]] = {}
        # Map transaction_id -> ProgressTracker
        self._trackers: Dict[str, 'ProgressTracker'] = {}
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """
        Register a WebSocket connection for a session
        
        Args:
            websocket: WebSocket connection
            session_id: Session ID
        """
        await websocket.accept()
        
        async with self._lock:
            if session_id not in self._connections:
                self._connections[session_id] = []
            self._connections[session_id].append(websocket)
            logger.info(f"WebSocket connected for session {session_id} (total: {len(self._connections[session_id])})")
    
    async def disconnect(self, websocket: WebSocket, session_id: str):
        """
        Unregister a WebSocket connection
        
        Args:
            websocket: WebSocket connection
            session_id: Session ID
        """
        async with self._lock:
            if session_id in self._connections:
                try:
                    self._connections[session_id].remove(websocket)
                    if not self._connections[session_id]:
                        del self._connections[session_id]
                    logger.info(f"WebSocket disconnected for session {session_id}")
                except ValueError:
                    pass
    
    def create_tracker(
        self,
        session_id: str,
        transaction_id: str
    ) -> 'ProgressTracker':
        """
        Create a progress tracker for a transaction
        
        Args:
            session_id: Session ID
            transaction_id: Transaction ID
            
        Returns:
            ProgressTracker instance
        """
        tracker = ProgressTracker(session_id, transaction_id, self)
        self._trackers[transaction_id] = tracker
        return tracker
    
    def get_tracker(self, transaction_id: str) -> Optional['ProgressTracker']:
        """
        Get progress tracker for a transaction
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            ProgressTracker instance or None
        """
        return self._trackers.get(transaction_id)
    
    async def send_update(self, session_id: str, update: ProgressUpdate):
        """
        Send progress update to all WebSocket connections for a session
        
        Args:
            session_id: Session ID
            update: Progress update
        """
        async with self._lock:
            connections = self._connections.get(session_id, [])
        
        if not connections:
            logger.debug(f"No WebSocket connections for session {session_id}")
            return
        
        message = json.dumps(update.to_dict())
        disconnected = []
        
        for websocket in connections:
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.warning(f"Error sending WebSocket message: {e}")
                disconnected.append(websocket)
        
        # Clean up disconnected connections
        if disconnected:
            async with self._lock:
                if session_id in self._connections:
                    for ws in disconnected:
                        try:
                            self._connections[session_id].remove(ws)
                        except ValueError:
                            pass
                    if not self._connections[session_id]:
                        del self._connections[session_id]
    
    def cleanup_tracker(self, transaction_id: str):
        """
        Clean up progress tracker
        
        Args:
            transaction_id: Transaction ID
        """
        if transaction_id in self._trackers:
            del self._trackers[transaction_id]


class ProgressTracker:
    """Tracks progress for a single transaction"""
    
    def __init__(
        self,
        session_id: str,
        transaction_id: str,
        manager: ProgressManager
    ):
        self.session_id = session_id
        self.transaction_id = transaction_id
        self.manager = manager
        self.current_agent: Optional[str] = None
        self.current_tasks: Dict[str, List[str]] = {}
        self.progress_events: List[ProgressEvent] = []
        self.execution_order: List[ExecutionOrderEntry] = []
    
    def start_agent(self, agent_name: str, tasks: Optional[List[str]] = None):
        """
        Mark agent as started
        
        Args:
            agent_name: Agent name
            tasks: List of tasks for this agent
        """
        self.current_agent = agent_name
        if tasks:
            self.current_tasks[agent_name] = tasks
        
        # Add execution order entry
        entry = ExecutionOrderEntry(agent_name, datetime.utcnow())
        self.execution_order.append(entry)
        
        # Add progress event
        event = ProgressEvent(
            agent=agent_name,
            event_type="agent_started",
            message=f"{agent_name} started execution"
        )
        self.progress_events.append(event)
        
        logger.debug(f"Agent {agent_name} started for transaction {self.transaction_id}")
        self._schedule_update()
    
    def complete_agent(self, agent_name: str):
        """
        Mark agent as completed
        
        Args:
            agent_name: Agent name
        """
        # Find execution order entry
        for entry in reversed(self.execution_order):
            if entry.agent == agent_name and entry.status == "running":
                entry.complete()
                break
        
        # Add progress event
        event = ProgressEvent(
            agent=agent_name,
            event_type="agent_completed",
            message=f"{agent_name} completed execution"
        )
        self.progress_events.append(event)
        
        # Clear current agent if it matches
        if self.current_agent == agent_name:
            self.current_agent = None
            if agent_name in self.current_tasks:
                del self.current_tasks[agent_name]
        
        logger.debug(f"Agent {agent_name} completed for transaction {self.transaction_id}")
        self._schedule_update()
    
    def fail_agent(self, agent_name: str, error: str):
        """
        Mark agent as failed
        
        Args:
            agent_name: Agent name
            error: Error message
        """
        # Find execution order entry
        for entry in reversed(self.execution_order):
            if entry.agent == agent_name and entry.status == "running":
                entry.fail()
                break
        
        # Add progress event
        event = ProgressEvent(
            agent=agent_name,
            event_type="agent_failed",
            message=f"{agent_name} failed: {error}",
            metadata={"error": error}
        )
        self.progress_events.append(event)
        
        # Clear current agent if it matches
        if self.current_agent == agent_name:
            self.current_agent = None
            if agent_name in self.current_tasks:
                del self.current_tasks[agent_name]
        
        logger.debug(f"Agent {agent_name} failed for transaction {self.transaction_id}")
        self._schedule_update()
    
    def add_event(
        self,
        agent_name: str,
        event_type: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Add a progress event
        
        Args:
            agent_name: Agent name
            event_type: Event type
            message: Event message
            metadata: Optional metadata
        """
        event = ProgressEvent(
            agent=agent_name,
            event_type=event_type,
            message=message,
            metadata=metadata or {}
        )
        self.progress_events.append(event)
        self._schedule_update()
    
    def _schedule_update(self):
        """Schedule an async update (thread-safe, fire-and-forget)"""
        import threading
        
        def run_update():
            """Run update in background thread with its own event loop"""
            # Create a new event loop for this thread
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                new_loop.run_until_complete(self._send_update())
            except Exception as e:
                logger.error(f"Error sending progress update: {e}")
            finally:
                new_loop.close()
        
        # Run in background thread to avoid blocking synchronous workflow execution
        thread = threading.Thread(target=run_update, daemon=True)
        thread.start()
    
    async def _send_update(self):
        """Send progress update via manager"""
        update = ProgressUpdate(
            session_id=self.session_id,
            transaction_id=self.transaction_id,
            current_agent=self.current_agent,
            current_tasks=self.current_tasks,
            progress_events=self.progress_events[-10:],  # Keep last 10 events
            execution_order=self.execution_order
        )
        await self.manager.send_update(self.session_id, update)


# Global progress manager instance
progress_manager = ProgressManager()
