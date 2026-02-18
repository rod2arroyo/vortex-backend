from fastapi import APIRouter, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.auth_service import AuthService
from app.schemas.auth import Token

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/google", response_model=Token)
async def login_google(
    db: AsyncSession = Depends(get_db),
    google_data: dict = Body(...) # Recibe {email, sub, name} desde el front
):
    return await AuthService.login_with_google(db, google_data)

@router.post("/refresh", response_model=Token)
async def refresh_session(
    refresh_token: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db)
):
    # Devuelve un nuevo access_token usando el refresh_token
    return await AuthService.refresh_token(db, refresh_token)