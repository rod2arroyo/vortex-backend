from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import User
from app.schemas.invitation import NotificationResponse
from app.models.notification import Notification

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("/", response_model=List[NotificationResponse])
async def get_my_notifications(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Trae las últimas 20 notificaciones"""
    query = (
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(20)
    )
    result = await db.execute(query)
    return result.scalars().all()

@router.patch("/{notification_id}/read")
async def mark_as_read(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Marca una notificación como leída (para apagar la luz roja)"""
    notif = await db.get(Notification, notification_id)
    if notif and notif.user_id == current_user.id:
        notif.is_read = True
        await db.commit()
    return {"ok": True}

@router.delete("/{notification_id}", status_code=status.HTTP_200_OK)
async def delete_notification(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Elimina una notificación específica.
    Útil para limpiar la bandeja o cuando se rechaza una invitación manualmente.
    """
    # 1. Buscamos la notificación asegurando que pertenezca al usuario actual
    query = select(Notification).where(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    )
    result = await db.execute(query)
    notification = result.scalars().first()

    if not notification:
        raise HTTPException(
            status_code=404,
            detail="Notificación no encontrada o no te pertenece"
        )

    # 2. Eliminamos
    await db.delete(notification)
    await db.commit()

    return {"message": "Notificación eliminada correctamente"}