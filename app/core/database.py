from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from pathlib import Path
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Motor asíncrono
engine = create_async_engine(DATABASE_URL, echo=True)

# Creador de sesiones
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Clase base para los modelos
class Base(DeclarativeBase):
    pass

# Dependencia para FastAPI
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session