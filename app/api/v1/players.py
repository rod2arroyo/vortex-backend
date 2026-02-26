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
        region: str,
        riot_nick: str,
        riot_tag: str,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    # 1. Validar si YO (el usuario actual) ya tengo una cuenta vinculada
    query_me = select(PlayerAccount).where(PlayerAccount.user_id == current_user.id)
    if (await db.execute(query_me)).scalars().first():
        raise HTTPException(status_code=400,
                            detail="Ya tienes una cuenta vinculada. Desvincúlala primero si quieres cambiar.")

    # 2. Obtener datos de Riot (Obtenemos el PUUID)
    riot_data = await RiotService.get_riot_account(riot_nick, riot_tag)
    puuid = riot_data["puuid"]

    # 3. NUEVA VALIDACIÓN: Verificar si la cuenta de RIOT ya está registrada en el sistema
    # Esto evita el error 500 "IntegrityError"
    query_puuid = select(PlayerAccount).where(PlayerAccount.puuid == puuid)
    account_owner = (await db.execute(query_puuid)).scalars().first()

    if account_owner:
        # Opcional: Podrías verificar si account_owner.user_id == current_user.id para dar un mensaje más específico
        raise HTTPException(status_code=409, detail="Esta cuenta de Riot ya está vinculada a otro usuario en Vortex.")

    # 4. Si pasamos las validaciones, creamos el registro
    new_account = PlayerAccount(
        user_id=current_user.id,
        riot_id=riot_data["gameName"],
        riot_tag=riot_data["tagLine"],
        region=region,
        puuid=puuid,
        current_rank="Unranked",  # Aquí podrías llamar a get_player_rank()
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