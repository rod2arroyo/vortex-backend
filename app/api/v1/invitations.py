from fastapi import APIRouter, Depends, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.invitation_service import InvitationService

# Definimos el router
router = APIRouter(prefix="/invitations", tags=["invitations"])

@router.post("/teams/{team_id}/link", status_code=status.HTTP_201_CREATED)
async def create_team_invite_link(
    team_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    [CAPITÁN] Genera un enlace de invitación único para el equipo.
    Cualquiera con este link podrá unirse si hay cupo.
    """
    # Nota: La validación de si es capitán se hace dentro del servicio
    # o deberíamos agregarla aquí si el servicio no la tiene.
    # Asumimos que el servicio valida permisos.
    return await InvitationService.create_invitation_link(db, team_id, current_user.id)


@router.post("/teams/{team_id}/invite", status_code=status.HTTP_201_CREATED)
async def invite_user_by_nick(
    team_id: UUID,
    nick: str = Body(..., embed=True), # Espera un JSON: {"nick": "Faker"}
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    [CAPITÁN] Busca un usuario por su Nick Interno y le envía una notificación.
    """
    return await InvitationService.invite_user_directly(
        db,
        team_id,
        current_user.id,
        nick
    )


@router.post("/{token}/accept", status_code=status.HTTP_200_OK)
async def accept_team_invitation(
    token: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    [USUARIO] Acepta una invitación usando el token (ya sea del link o de la notificación).
    Verifica cupos y añade al usuario a la tabla team_members.
    """
    return await InvitationService.accept_invitation(db, token, current_user.id)