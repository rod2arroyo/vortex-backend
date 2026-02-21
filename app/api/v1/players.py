from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User, PlayerAccount
from app.services.riot_service import RiotService
from sqlalchemy import select

router = APIRouter(prefix="/players", tags=["players"])

@router.post("/link-riot")
async def link_riot_account(
        region: str,  # LAN, LAS, BR
        riot_nick: str,
        riot_tag: str,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    # 1. Validar si ya tiene una cuenta vinculada
    query = select(PlayerAccount).where(PlayerAccount.user_id == current_user.id)
    existing = (await db.execute(query)).scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="Ya tienes una cuenta vinculada")

    # 2. Validar existencia en Riot
    riot_data = await RiotService.get_riot_account(riot_nick, riot_tag)

    # 3. Crear registro en nuestra tabla
    new_account = PlayerAccount(
        user_id=current_user.id,
        riot_id=riot_data["gameName"],
        riot_tag=riot_data["tagLine"],
        region=region,
        puuid=riot_data["puuid"],
        current_rank="Unranked",
        is_verified=False
    )

    db.add(new_account)
    await db.commit()
    return {"message": "Cuenta vinculada exitosamente", "data": riot_data}


@router.get("/riot-profile")
async def get_riot_profile(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    # 1. Buscar la cuenta en tu DB (donde ya guardaste el PUUID)
    query = select(PlayerAccount).where(PlayerAccount.user_id == current_user.id)
    player_acc = (await db.execute(query)).scalars().first()

    if not player_acc:
        raise HTTPException(status_code=404, detail="No tienes una cuenta vinculada")

    # 2. Llamada directa por PUUID usando el nuevo método
    ranks = await RiotService.get_rank_data_by_puuid(player_acc.region, player_acc.puuid)

    return {
        "riot_id": player_acc.riot_id,
        "riot_tag": player_acc.riot_tag,
        "region": player_acc.region,
        "ranks": ranks
    }