from pydantic import BaseModel, EmailStr, Field, ConfigDict, computed_field
from typing import Optional
from uuid import UUID

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    google_id: str

class UserOnboarding(BaseModel):
    """Datos obligatorios tras el primer login con Google"""
    internal_nick: str = Field(
        ...,
        min_length=3,
        max_length=20,
        pattern=r"^[a-zA-Z0-9_]+$",
        description="Solo letras, números y guiones bajos."
    )
    whatsapp: str = Field(..., pattern=r"^\+?[1-9]\d{1,14}$")
    country: str = Field(..., min_length=2, max_length=50)

class UserUpdate(BaseModel):
    """Campos que el usuario puede editar después"""
    internal_nick: Optional[str] = Field(None, min_length=3, max_length=20, pattern=r"^[a-zA-Z0-9_]+$")
    whatsapp: Optional[str] = Field(None, pattern=r"^\+?[1-9]\d{1,14}$")
    country: Optional[str] = None


class UserResponse(UserBase):
    id: UUID
    internal_nick: Optional[str] = None
    whatsapp: Optional[str] = None
    country: Optional[str] = None

    # ELIMINA la variable estática: is_onboarded: bool = False

    # AGREGA esto:
    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def is_onboarded(self) -> bool:
        return self.internal_nick is not None