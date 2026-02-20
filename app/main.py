from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.api.v1 import auth, user, players, teams

app = FastAPI(title="Vortex Esports API")

# Configuración de CORS
origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    # Aquí podrías agregar el dominio de tu frontend de TikTok/Web más adelante
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En desarrollo puedes usar ["*"] para permitir todo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(user.router, prefix="/api/v1")

app.include_router(players.router, prefix="/api/v1")

app.include_router(teams.router, prefix="/api/v1")