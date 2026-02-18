from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timezone, timedelta

from app.models import user
from app.models.user import User, RefreshToken
from app.core.security import create_access_token, create_refresh_token
from app.core.config import settings


class AuthService:
    @staticmethod
    async def login_with_google(db: AsyncSession, google_data: dict):
        # 1. Intentar buscar al usuario
        query = select(User).where(User.google_id == google_data["sub"])
        result = await db.execute(query)
        user = result.scalars().first()

        # 2. Si es nuevo, crearlo
        if not user:
            user = User(
                email=google_data["email"],
                google_id=google_data["sub"]
            )
            db.add(user)
            # El flush genera el user.id pero NO cierra la transacción
            await db.flush()

            # 3. Generar tokens (Convertir UUID a string es obligatorio para JWT)
        user_id_str = str(user.id)
        access_token = create_access_token(subject=user_id_str)
        refresh_token_str = create_refresh_token(subject=user_id_str)

        # 4. Guardar Refresh Token
        db_refresh = RefreshToken(
            user_id=user.id,
            token=refresh_token_str,
            # Aseguramos que la fecha sea UTC
            expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=7)
        )
        db.add(db_refresh)

        # 5. Guardar todo en la DB
        await db.commit()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token_str,
            "token_type": "bearer"
        }

    @staticmethod
    async def refresh_token(db: AsyncSession, token: str):
        # 1. Limpieza de seguridad: quitamos "Bearer " si el usuario lo incluyó por error
        if token.startswith("Bearer "):
            token = token.replace("Bearer ", "").strip()
        else:
            token = token.strip()

        # 2. Búsqueda exacta en la DB
        result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.token == token,
                RefreshToken.revoked == False
            )
        )
        db_token = result.scalars().first()

        if not db_token:
            print(f"DEBUG: Token no encontrado en DB. Enviado: {token[:10]}...")
            raise HTTPException(status_code=401, detail="Refresh token inválido o revocado")

        # 3. Validación de expiración con Timezones (UTC)
        now = datetime.now(timezone.utc)
        # Si tu DB guarda naive, lo forzamos a UTC para comparar
        token_expiry = db_token.expires_at.replace(tzinfo=timezone.utc)

        if token_expiry < now:
            print(f"DEBUG: Token expirado el {token_expiry}. Ahora es {now}")
            raise HTTPException(status_code=401, detail="Refresh token ha expirado")

        # 4. Generación de nuevo acceso
        # Convertimos el UUID del user_id a string para el JWT
        new_access = create_access_token(subject=str(db_token.user_id))

        return {
            "access_token": new_access,
            "token_type": "bearer",
            "refresh_token": token  # Devolvemos el mismo o uno nuevo (rotación)
        }