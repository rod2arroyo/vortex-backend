from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException
from uuid import UUID

from sqlalchemy.orm import selectinload

from app.models.tournament import Tournament
from app.schemas.tournament import TournamentCreate, TournamentUpdate

class TournamentService:
    @staticmethod
    async def create_tournament(db: AsyncSession, data: TournamentCreate):
        new_tournament = Tournament(
            name=data.name,
            description=data.description,
            category=data.category,
            entry_fee=data.entry_fee,
            prize_pool=data.prize_pool,
            max_teams=data.max_teams,
            start_date=data.start_date
        )
        db.add(new_tournament)
        await db.commit()
        await db.refresh(new_tournament)
        return new_tournament

    @staticmethod
    async def update_tournament(db: AsyncSession, tournament_id: UUID, data: TournamentUpdate):
        query = select(Tournament).where(Tournament.id == tournament_id)
        result = await db.execute(query)
        tournament = result.scalars().first()

        if not tournament:
            raise HTTPException(status_code=404, detail="Torneo no encontrado")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(tournament, key, value)

        await db.commit()
        await db.refresh(tournament)
        return tournament

    @staticmethod
    async def get_all_tournaments(db: AsyncSession, skip: int = 0, limit: int = 20):
        """
        Obtiene lista de torneos con paginación básica.
        Carga 'registrations' solo para hacer el conteo.
        """
        query = (
            select(Tournament)
            .options(selectinload(Tournament.registrations))  # Vital para el conteo
            .order_by(Tournament.start_date.desc())  # Ordenamos por fecha
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_tournament_by_id(db: AsyncSession, tournament_id: UUID):
        """Obtiene el detalle de un torneo específico"""
        query = (
            select(Tournament)
            .where(Tournament.id == tournament_id)
            .options(selectinload(Tournament.registrations))
        )
        result = await db.execute(query)
        tournament = result.scalars().first()

        if not tournament:
            raise HTTPException(status_code=404, detail="Torneo no encontrado")

        return tournament