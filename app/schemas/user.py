from pydantic import BaseModel, EmailStr, Field, ConfigDict, computed_field
from typing import Optional
from uuid import UUID

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    google_id: str


class UserOnboarding(BaseModel):
    """Datos obligatorios tras el primer login"""
    internal_nick: str = Field(
        ...,
        min_length=3,
        max_length=20,
        pattern=r"^[a-zA-Z0-9_]+$",
        description="Solo letras, números y guiones bajos."
    )
    country: str = Field(..., min_length=2, max_length=50)

    # Nuevos campos obligatorios
    phone_country_code: str = Field(..., pattern=r"^\+\d{1,4}$", description="Ej: +51")
    phone_number: str = Field(..., pattern=r"^\d{7,15}$", description="Solo dígitos")
    discord_id: str = Field(..., min_length=2, max_length=32)


class UserUpdate(BaseModel):
    """Campos opcionales para edición de perfil"""
    internal_nick: Optional[str] = Field(None, min_length=3, max_length=20, pattern=r"^[a-zA-Z0-9_]+$")
    country: Optional[str] = None
    phone_country_code: Optional[str] = Field(None, pattern=r"^\+\d{1,4}$")
    phone_number: Optional[str] = Field(None, pattern=r"^\d{7,15}$")
    discord_id: Optional[str] = Field(None, min_length=2, max_length=32)


class UserResponse(UserBase):
    id: UUID
    google_id: Optional[str] = None
    internal_nick: Optional[str] = None
    country: Optional[str] = None

    # Nuevos campos en la respuesta
    phone_country_code: Optional[str] = None
    phone_number: Optional[str] = None
    discord_id: Optional[str] = None

    role: str

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def is_onboarded(self) -> bool:
        # Se considera onboarded si tiene nick y teléfono configurado
        return self.internal_nick is not None and self.phone_number is not None