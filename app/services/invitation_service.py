import secrets
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from fastapi import HTTPException
from datetime import datetime, timezone, timedelta
from app.models.invitation import TeamInvitation, InvitationStatus
from app.models.team import Team, TeamMember
from app.models.notification import Notification
from app.models.user import User

class InvitationService:

    @staticmethod
    async def create_invitation_link(db: AsyncSession, team_id: str, inviter_id: str):
        """Genera un link único que cualquiera puede usar"""
        token = secrets.token_urlsafe(16)  # Genera string aleatorio seguro
        invite = TeamInvitation(
            team_id=team_id,
            inviter_id=inviter_id,
            token=token,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
            status=InvitationStatus.PENDING
        )
        db.add(invite)
        await db.commit()
        # Frontend construirá: https://vortex.gg/invite/{token}
        return {"link_token": token}

    @staticmethod
    async def invite_user_directly(db: AsyncSession, team_id: str, inviter_id: str, target_user_nick: str):
        """Busca usuario por nick, crea invitación y notifica"""
        # 1. Buscar usuario destino
        query = select(User).where(User.internal_nick == target_user_nick)
        target_user = (await db.execute(query)).scalars().first()

        if not target_user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # 2. Verificar que no esté ya en el equipo
        member_check = select(TeamMember).where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == target_user.id
        )
        if (await db.execute(member_check)).scalars().first():
            raise HTTPException(status_code=400, detail="El usuario ya está en el equipo")

        # 3. Crear invitación
        token = secrets.token_urlsafe(16)
        invite = TeamInvitation(
            team_id=team_id,
            inviter_id=inviter_id,
            invitee_id=target_user.id,
            token=token,
            expires_at=datetime.now(timezone.utc) + timedelta(days=2),
        )
        db.add(invite)

        # 4. CREAR NOTIFICACIÓN
        # Obtenemos nombre del equipo para el mensaje
        team = await db.get(Team, team_id)
        notification = Notification(
            user_id=target_user.id,
            type="TEAM_INVITE",
            title="Invitación de Equipo",
            message=f"Te han invitado a unirte al equipo {team.name}",
            data={"team_id": str(team_id), "token": token}
        )
        db.add(notification)

        await db.commit()
        return {"message": f"Invitación enviada a {target_user_nick}"}

    @staticmethod
    async def accept_invitation(db: AsyncSession, token: str, user_id: str):
        """Lógica para procesar la aceptación"""
        # 1. Validar token
        query = select(TeamInvitation).where(
            TeamInvitation.token == token,
            TeamInvitation.status == InvitationStatus.PENDING,
            TeamInvitation.expires_at > datetime.now(timezone.utc)
        )
        invite = (await db.execute(query)).scalars().first()

        if not invite:
            raise HTTPException(status_code=404, detail="Invitación inválida o expirada")

        # 2. Validar Cupos (Max 6)
        count_query = select(func.count()).select_from(TeamMember).where(TeamMember.team_id == invite.team_id)
        current_members = (await db.execute(count_query)).scalar()

        if current_members >= 6:
            raise HTTPException(status_code=400, detail="El equipo ya está lleno (6/6)")

        # 3. Añadir a TeamMember
        new_member = TeamMember(team_id=invite.team_id, user_id=user_id)
        db.add(new_member)

        # 4. Actualizar estado de invitación
        invite.status = InvitationStatus.ACCEPTED
        invite.invitee_id = user_id  # Vinculamos por si era un link anónimo

        await db.commit()
        return {"message": "Bienvenido al equipo!"}