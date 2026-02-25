from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class TeamBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=25)
    tag: str = Field(..., min_length=3, max_length=5, description="Tag del equipo (ej. T1, G2)")
    description: Optional[str] = None

class TeamCreate(TeamBase):
    pass

class TeamUpdate(BaseModel):
    """Todos los campos son opcionales para permitir actualizaciones parciales (PATCH)"""
    name: Optional[str] = Field(None, min_length=3, max_length=25)
    description: Optional[str] = None
    logo_url: Optional[str] = None # Listo para S3 en el futuro


class TeamMemberResponse(BaseModel):
    user_id: UUID
    joined_at: datetime

    # AGREGAMOS ESTOS DOS CAMPOS:
    player_name: str  # El nick de la página (Vortex)
    riot_id_full: Optional[str] = None  # El nick del juego (LoL)

    class Config:
        from_attributes = True

class TeamResponse(TeamBase):
    id: UUID
    captain_id: UUID
    logo_url: Optional[str]
    created_at: datetime
    members: List[TeamMemberResponse] = []

    class Config:
        from_attributes = True