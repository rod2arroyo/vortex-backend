import httpx
from fastapi import HTTPException
from app.core.config import settings


class RiotService:
    HEADERS = {"X-Riot-Token": settings.RIOT_API_KEY}

    # Mapeo de regiones para la API
    REGION_MAP = {
        "LAN": "la1",
        "LAS": "la2",
        "BR": "br1"
    }

    @classmethod
    async def get_riot_account(cls, game_name: str, tag_line: str):
        """Busca el PUUID por Riot ID (Nick#Tag)"""
        url = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=cls.HEADERS)
            if response.status_code != 200:
                raise HTTPException(status_code=404, detail="Cuenta de Riot no encontrada")
            return response.json()  # Devuelve puuid, gameName, tagLine

    @classmethod
    async def get_summoner_data(cls, region: str, puuid: str):
        """Obtiene ID de invocador y nivel"""
        platform = cls.REGION_MAP.get(region)
        url = f"https://{platform}.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=cls.HEADERS)
            return response.json()

    @classmethod
    async def get_rank_data(cls, region: str, summoner_id: str):
        """Obtiene el rango (SoloQ/Flex)"""
        platform = cls.REGION_MAP.get(region)
        url = f"https://{platform}.api.riotgames.com/lol/league/v4/entries/by-summoner/{summoner_id}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=cls.HEADERS)
            return response.json()

    @classmethod
    async def get_rank_data_by_puuid(cls, region: str, puuid: str):
        """
        Usa el endpoint de LEAGUE-V4 directo por PUUID
        visto en tu captura de APIs habilitadas.
        """
        platform = cls.REGION_MAP.get(region)
        # Endpoint: /lol/league/v4/entries/by-puuid/{encryptedPUUID}
        url = f"https://{platform}.api.riotgames.com/lol/league/v4/entries/by-puuid/{puuid}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=cls.HEADERS)

            if response.status_code != 200:
                error_info = response.json().get("status", {})
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Error de Riot ({error_info.get('status_code')}): {error_info.get('message')}"
                )

            return response.json()