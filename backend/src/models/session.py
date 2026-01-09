from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any


class Session(BaseModel):
    session_id: str
    user_id: str
    created_at: datetime
    expires_at: datetime
    last_activity: datetime
    metadata: Dict[str, Any] = {}

