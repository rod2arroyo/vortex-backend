from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.user import UserOnboarding, UserUpdate
from uuid import UUID

class UserService:
    @staticmethod
    async def get_user_by_google_id(db: AsyncSession, google_id: str):
        result = await db.execute(select(User).where(User.google_id == google_id))
        return result.scalars().first()

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
        # 1. Validar que el nick no esté tomado
        if await UserService.check_nick_exists(db, data.internal_nick):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El Nick Interno ya está en uso."
            )

        # 2. Actualizar datos de perfil
        query = (
            update(User)
            .where(User.id == user_id)
            .values(
                internal_nick=data.internal_nick,
                whatsapp=data.whatsapp,
                country=data.country
            )
        )
        await db.execute(query)
        await db.commit()
        return await UserService.get_user_by_id(db, user_id)

    @staticmethod
    async def update_profile(db: AsyncSession, user_id: UUID, data: UserUpdate):
        # 1. Limpieza de seguridad: Evitamos que inyecten campos protegidos
        update_data = data.model_dump(exclude_unset=True)

        # Lista de campos que NUNCA se deben actualizar por este endpoint
        for field in ["is_onboarded", "id", "role", "email"]:
            update_data.pop(field, None)

        # 2. Validación de Nickname único (si aplica)
        if "internal_nick" in update_data:
            # Buscamos si existe alguien MÁS con ese nick (excluyendo al usuario actual)
            query_check = select(User).where(
                User.internal_nick == update_data["internal_nick"],
                User.id != user_id
            )
            if (await db.execute(query_check)).scalars().first():
                raise HTTPException(status_code=400, detail="Este nickname ya está en uso.")

        # 3. Ejecutar actualización solo si hay datos válidos
        if update_data:
            query_update = update(User).where(User.id == user_id).values(**update_data)
            await db.execute(query_update)
            await db.commit()

        # 4. Retornar el usuario actualizado
        return await UserService.get_user_by_id(db, user_id)