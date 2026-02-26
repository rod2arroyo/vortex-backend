import secrets
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, delete
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
    async def accept_invitation(db: AsyncSession, token: str, user_id: UUID):
        """Lógica para procesar la aceptación de invitación a equipo"""

        # 1. Validar token (Existencia, Estado y Expiración)
        query = select(TeamInvitation).where(
            TeamInvitation.token == token,
            TeamInvitation.status == InvitationStatus.PENDING,
            TeamInvitation.expires_at > datetime.now(timezone.utc)
        )
        invite = (await db.execute(query)).scalars().first()

        if not invite:
            raise HTTPException(status_code=404, detail="Invitación inválida, expirada o ya utilizada")

        # 2. VALIDACIÓN CRÍTICA: ¿El usuario ya está en el equipo?
        # Esto previene duplicados antes de chequear cupos
        member_check = select(TeamMember).where(
            TeamMember.team_id == invite.team_id,
            TeamMember.user_id == user_id
        )
        if (await db.execute(member_check)).scalars().first():
            raise HTTPException(status_code=400, detail="Ya eres miembro de este equipo")

        # 3. Validar Cupos (Max 6)
        count_query = select(func.count()).select_from(TeamMember).where(TeamMember.team_id == invite.team_id)
        current_members = (await db.execute(count_query)).scalar()

        if current_members >= 6:
            raise HTTPException(status_code=400, detail="El equipo ya está lleno (6/6)")

        # 4. Añadir a TeamMember
        new_member = TeamMember(team_id=invite.team_id, user_id=user_id)
        db.add(new_member)

        # 5. Actualizar estado de la invitación
        invite.status = InvitationStatus.ACCEPTED
        invite.invitee_id = user_id  # Registramos quién usó el token

        # 6. LIMPIEZA AUTOMÁTICA DE NOTIFICACIONES
        # Buscamos y eliminamos la notificación asociada a este token para este usuario
        # Usamos cast de JSON si es necesario, pero SQLAlchemy suele manejarlo bien así:
        try:
            cleanup_query = delete(Notification).where(
                Notification.user_id == user_id,
                Notification.type == "TEAM_INVITE",
                # Postgres JSONB: busca dentro del objeto data la clave token
                Notification.data['token'].astext == token
            )
            await db.execute(cleanup_query)
        except Exception as e:
            # No queremos que falle el ingreso al equipo si falla el borrado de notificación
            print(f"Warning: No se pudo borrar la notificación automática: {e}")

        await db.commit()
        return {"message": "¡Bienvenido al equipo! Has sido añadido exitosamente."}