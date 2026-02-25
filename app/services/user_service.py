from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.user import UserOnboarding, UserUpdate
from uuid import UUID


class UserService:
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: UUID):
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalars().first()

    @staticmethod
    async def check_nick_exists(db: AsyncSession, nick: str) -> bool:
        result = await db.execute(select(User).where(User.internal_nick == nick))
        return result.scalars().first() is not None

    @staticmethod
    async def onboard_user(db: AsyncSession, user_id: UUID, data: UserOnboarding):
        # 1. Validar unicidad del Nick
        if await UserService.check_nick_exists(db, data.internal_nick):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El Nick Interno ya está en uso."
            )

        # 2. Actualizar datos con los nuevos campos
        query = (
            update(User)
            .where(User.id == user_id)
            .values(
                internal_nick=data.internal_nick,
                country=data.country,
                phone_country_code=data.phone_country_code,
                phone_number=data.phone_number,
                discord_id=data.discord_id
            )
        )
        await db.execute(query)
        await db.commit()

        # Retornar usuario actualizado
        return await UserService.get_user_by_id(db, user_id)

    @staticmethod
    async def update_profile(db: AsyncSession, user_id: UUID, data: UserUpdate):
        # 1. Limpieza de seguridad
        update_data = data.model_dump(exclude_unset=True)

        # Proteger campos sensibles
        for field in ["id", "role", "email", "google_id", "is_onboarded"]:
            update_data.pop(field, None)

        # 2. Si se intenta cambiar el nick, verificar que no esté usado por otro
        if "internal_nick" in update_data:
            current_nick = update_data["internal_nick"]
            query_check = select(User).where(
                User.internal_nick == current_nick,
                User.id != user_id  # Excluir al usuario actual de la búsqueda
            )
            if (await db.execute(query_check)).scalars().first():
                raise HTTPException(status_code=400, detail="Este nickname ya está en uso.")

        # 3. Ejecutar update si hay datos
        if update_data:
            query_update = update(User).where(User.id == user_id).values(**update_data)
            await db.execute(query_update)
            await db.commit()

        return await UserService.get_user_by_id(db, user_id)