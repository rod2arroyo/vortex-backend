from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any


# --- Schemas para Invitaciones ---
class InvitationCreateLink(BaseModel):
    expiration_hours: int = 24  # Duración del link


class InvitationResponse(BaseModel):
    token: str
    team_name: str
    expires_at: datetime


# --- Schemas para Notificaciones ---
class NotificationResponse(BaseModel):
    id: UUID
    type: str
    title: str
    message: str
    data: Optional[Dict[str, Any]] = None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True