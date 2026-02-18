from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.schemas.user import UserResponse, UserOnboarding, UserUpdate
from app.services.user_service import UserService
from app.models.user import User

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=UserResponse)
async def read_user_me(current_user: User = Depends(get_current_user)):
    """Obtiene el perfil del usuario logueado"""
    return current_user

@router.post("/onboarding", response_model=UserResponse)
async def complete_onboarding(
    data: UserOnboarding,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Primer registro de Nick, WhatsApp y País"""
    return await UserService.onboard_user(db, current_user.id, data)

@router.patch("/update", response_model=UserResponse)
async def update_profile(
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Edición de datos existentes"""
    return await UserService.update_profile(db, current_user.id, data)