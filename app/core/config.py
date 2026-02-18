from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # --- Seguridad y JWT ---
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    RIOT_API_KEY: str

    # --- Google OAuth ---
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str

    # --- Base de Datos ---
    # Se añade aquí para que Pydantic la reconozca desde el .env
    DATABASE_URL: str

    # --- Configuración de Pydantic ---
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        # 'ignore' evita errores si hay variables en el .env que no declaraste aquí
        extra="ignore"
    )

settings = Settings()