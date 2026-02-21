from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload  # Clave para evitar el MissingGreenlet

from app.models import User
from app.models.team import Team, TeamMember
from app.schemas.team import TeamUpdate, TeamCreate

class TeamService:
    @staticmethod
    async def create_team(db: AsyncSession, data: TeamCreate, captain_id: UUID):
        # 1. Validar nombre o tag duplicado
        query = select(Team).where((Team.name == data.name) | (Team.tag == data.tag))
        existing_team = (await db.execute(query)).scalars().first()
        if existing_team:
            if existing_team.name == data.name:
                raise HTTPException(status_code=400, detail="El nombre del equipo ya está en uso.")
            raise HTTPException(status_code=400, detail="El tag del equipo ya está en uso.")

        # 2. Crear equipo (logo_url queda en None por defecto de la DB)
        new_team = Team(
            name=data.name,
            tag=data.tag.upper(),
            description=data.description,
            captain_id=captain_id
        )
        db.add(new_team)
        await db.flush()

        # 3. Agregar al capitán
        membership = TeamMember(team_id=new_team.id, user_id=captain_id)
        db.add(membership)
        await db.commit()

        # 4. Traer los datos completos para el Response (Deep Join)
        final_query = (
            select(Team)
            .where(Team.id == new_team.id)
            .options(
                selectinload(Team.members)
                .selectinload(TeamMember.user)
                .selectinload(User.player_accounts)
            )
        )
        result = await db.execute(final_query)
        return result.scalars().first()

    @staticmethod
    async def update_team(db: AsyncSession, team_id: UUID, data: TeamUpdate, user_id: UUID):
        # Usamos Deep Join para que la respuesta devuelva los miembros intactos
        query = (
            select(Team)
            .where(Team.id == team_id)
            .options(
                selectinload(Team.members)
                .selectinload(TeamMember.user)
                .selectinload(User.player_accounts)
            )
        )
        team = (await db.execute(query)).scalars().first()

        if not team:
            raise HTTPException(status_code=404, detail="Equipo no encontrado")
        if team.captain_id != user_id:
            raise HTTPException(status_code=403, detail="Solo el capitán puede editar el equipo")

        # Actualización dinámica de campos
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(team, key, value)

        await db.commit()
        await db.refresh(team)
        return team

    @staticmethod
    async def get_user_teams(db: AsyncSession, user_id: UUID):
        """Retorna la lista de equipos y todo el árbol de relaciones necesario"""
        query = (
            select(Team)
            .join(TeamMember, Team.id == TeamMember.team_id)
            .where(TeamMember.user_id == user_id)
            .options(
                selectinload(Team.members)
                .selectinload(TeamMember.user)
                .selectinload(User.player_accounts)
            )
        )
        result = await db.execute(query)
        return result.scalars().unique().all()

    @staticmethod
    async def remove_member(db: AsyncSession, team_id: UUID, user_to_remove_id: UUID, captain_id: UUID):
        """Permite al capitán expulsar a un miembro"""
        # 1. Verificar que el equipo existe y el solicitante es el capitán
        query_team = select(Team).where(Team.id == team_id)
        team = (await db.execute(query_team)).scalars().first()

        if not team:
            raise HTTPException(status_code=404, detail="Equipo no encontrado")
        if team.captain_id != captain_id:
            raise HTTPException(status_code=403, detail="Solo el capitán puede retirar integrantes")
        if user_to_remove_id == captain_id:
            raise HTTPException(status_code=400,
                                detail="El capitán no puede expulsarse a sí mismo. Debe disolver el equipo.")

        # 2. Proceder con la eliminación
        query_member = delete(TeamMember).where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_to_remove_id
        )
        result = await db.execute(query_member)

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="El usuario no pertenece a este equipo")

        await db.commit()
        return {"message": "Integrante retirado exitosamente"}

    @staticmethod
    async def leave_team(db: AsyncSession, team_id: UUID, user_id: UUID):
        """Permite a un participante abandonar el equipo"""
        # 1. Verificar si es el capitán
        query_team = select(Team).where(Team.id == team_id)
        team = (await db.execute(query_team)).scalars().first()

        if team and team.captain_id == user_id:
            raise HTTPException(
                status_code=400,
                detail="El capitán no puede abandonar el equipo. Debe nombrar un nuevo capitán o disolverlo."
            )

        # 2. Eliminar la membresía
        query_member = delete(TeamMember).where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id
        )
        result = await db.execute(query_member)

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="No eres miembro de este equipo")

        await db.commit()
        return {"message": "Has abandonado el equipo correctamente"}

    @staticmethod
    async def delete_team(db: AsyncSession, team_id: UUID, captain_id: UUID):
        """Permite al capitán disolver/eliminar el equipo por completo"""
        # 1. Buscar el equipo
        query = select(Team).where(Team.id == team_id)
        result = await db.execute(query)
        team = result.scalars().first()

        # 2. Validaciones de seguridad
        if not team:
            raise HTTPException(status_code=404, detail="Equipo no encontrado")

        if team.captain_id != captain_id:
            raise HTTPException(
                status_code=403,
                detail="Solo el capitán tiene los permisos para eliminar el equipo"
            )

        # 3. Eliminar el equipo
        # los registros en team_members se borrarán automáticamente.
        await db.delete(team)
        await db.commit()

        return {"message": f"El equipo '{team.name}' ha sido disuelto exitosamente"}