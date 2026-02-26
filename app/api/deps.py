from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import decode_token
from app.models import User, UserRole
from app.services.user_service import UserService

# 1. Definimos el esquema como HTTPBearer
security = HTTPBearer()


async def get_current_user(
        db: AsyncSession = Depends(get_db),
        # 2. Ahora depende de 'security' y recibimos un objeto de credenciales
        auth: HTTPAuthorizationCredentials = Depends(security)
):
    # 3. Extraemos el token real del campo 'credentials'
    token = auth.credentials

    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
        )

    user_id = payload.get("sub")
    user = await UserService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return user

def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Valida que el usuario logueado tenga el rol de ADMIN.
    Si es PLAYER, lanza un error 403 Forbidden.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos de administrador para realizar esta acción."
        )
    return current_user