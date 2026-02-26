from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.database import get_db
from app.api.deps import get_current_admin
from app.schemas.tournament import TournamentCreate, TournamentUpdate, TournamentResponse, TournamentListResponse, \
    TournamentDetailResponse
from app.services.tournament_service import TournamentService
from app.models.user import User

router = APIRouter(prefix="/tournaments", tags=["tournaments"])

@router.post("/", response_model=TournamentResponse, status_code=status.HTTP_201_CREATED)
async def create_tournament(
    data: TournamentCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin) # Solo Admins
):
    """Crea un nuevo torneo (Requiere permisos de Admin)"""
    return await TournamentService.create_tournament(db, data)

@router.patch("/{tournament_id}", response_model=TournamentResponse)
async def update_tournament(
    tournament_id: UUID,
    data: TournamentUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin) # Solo Admins
):
    """Actualiza datos del torneo (Estado, Premios, etc.)"""
    return await TournamentService.update_tournament(db, tournament_id, data)

@router.get("/", response_model=List[TournamentListResponse])
async def list_tournaments(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """
    Lista todos los torneos disponibles (Público).
    Muestra: Nombre, Modo, Premio, Equipos Inscritos, Fecha y Estado.
    """
    return await TournamentService.get_all_tournaments(db, skip, limit)

@router.get("/{tournament_id}", response_model=TournamentDetailResponse)
async def get_tournament_details(
    tournament_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene toda la información detallada de un torneo (Público).
    """
    return await TournamentService.get_tournament_by_id(db, tournament_id)