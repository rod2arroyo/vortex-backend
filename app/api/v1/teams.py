from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user
from app.schemas.team import TeamCreate, TeamUpdate, TeamResponse
from app.services.team_service import TeamService
from app.models.user import User
from uuid import UUID

router = APIRouter(prefix="/teams", tags=["teams"])

@router.post("/", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_new_team(
    data: TeamCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Crea un equipo (Nombre, Tag, Descripcion) y asigna al usuario como capitán"""
    return await TeamService.create_team(db, data, current_user.id)

@router.patch("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: UUID,
    data: TeamUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """[CAPITÁN] Permite actualizar nombre, descripción o logo"""
    return await TeamService.update_team(db, team_id, data, current_user.id)

@router.get("/my-teams", response_model=List[TeamResponse])
async def get_my_teams(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retorna los equipos a los que perteneces, listando a todos sus miembros y cuentas de Riot"""
    return await TeamService.get_user_teams(db, current_user.id)

@router.delete("/{team_id}/members/{user_id}")
async def remove_team_member(
    team_id: UUID,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """[CAPITÁN] Expulsa a un integrante del equipo"""
    return await TeamService.remove_member(db, team_id, user_id, current_user.id)

@router.delete("/{team_id}/leave")
async def leave_from_team(
    team_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """[PARTICIPANTE] Abandona el equipo actual"""
    return await TeamService.leave_team(db, team_id, current_user.id)

@router.delete("/{team_id}", status_code=status.HTTP_200_OK)
async def delete_team(
    team_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """[CAPITÁN] Elimina permanentemente el equipo y desvincula a todos sus miembros"""
    return await TeamService.delete_team(db, team_id, current_user.id)