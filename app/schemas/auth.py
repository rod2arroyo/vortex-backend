from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None # Hazlo opcional
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    """Lo que extraemos del JWT decodificado"""
    sub: Optional[str] = None
    type: Optional[str] = None

class GoogleAuthRequest(BaseModel):
    """El token que el frontend recibe de Google y nos envía"""
    token: str