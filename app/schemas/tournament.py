from pydantic import BaseModel, Field, computed_field, ConfigDict
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from app.models.tournament import TournamentStatus


class TournamentBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = None
    category: str = Field(..., description="Ej: Low Elo, High Elo, Open")
    entry_fee: float = Field(0.0, ge=0)
    prize_pool: float = Field(0.0, ge=0)
    max_teams: int = Field(16, ge=2, le=128)
    start_date: Optional[datetime] = None


class TournamentCreate(TournamentBase):
    pass


class TournamentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    entry_fee: Optional[float] = None
    prize_pool: Optional[float] = None
    max_teams: Optional[int] = None
    start_date: Optional[datetime] = None
    status: Optional[TournamentStatus] = None


class TournamentResponse(TournamentBase):
    id: UUID
    status: TournamentStatus

    class Config:
        from_attributes = True


class TournamentListResponse(BaseModel):
    """Información ligera para el listado público"""
    id: UUID
    name: str
    category: str
    entry_fee: float
    prize_pool: float
    max_teams: int
    start_date: Optional[datetime]
    status: TournamentStatus

    registrations: List[object] = Field(default=[], exclude=True)

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def registered_teams_count(self) -> int:
        """Calcula cuántos equipos hay inscritos"""
        return len(self.registrations)


class TournamentDetailResponse(TournamentListResponse):
    description: Optional[str]
    created_at: Optional[datetime] = None