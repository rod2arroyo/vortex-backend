from datetime import datetime, timezone
import enum

from sqlalchemy import Column, String, Boolean, UUID, ForeignKey, Enum, DateTime
from sqlalchemy.orm import relationship
import uuid
from app.core.database import Base


class UserRole(enum.Enum):
    PLAYER = "player"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True)
    google_id = Column(String, unique=True)

    # Campos de perfil (Nullable para el inicio, obligatorios tras onboarding)
    internal_nick = Column(String, unique=True, index=True, nullable=True)
    country = Column(String, nullable=True)

    # NUEVOS CAMPOS
    phone_country_code = Column(String, nullable=True)  # Ej: "+51"
    phone_number = Column(String, nullable=True)  # Ej: "999888777"
    discord_id = Column(String, nullable=True)  # Ej: "usuario_discord"

    role = Column(Enum(UserRole), default=UserRole.PLAYER)

    # Relaciones
    memberships = relationship("TeamMember", back_populates="user")
    player_accounts = relationship("PlayerAccount", back_populates="user")
    refresh_tokens = relationship("RefreshToken", back_populates="user")

class PlayerAccount(Base):
    __tablename__ = "player_accounts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))  # Sin unique=True
    riot_id = Column(String)
    riot_tag = Column(String)
    region = Column(String)  # IMPORTANTE: 'la1', 'la2' o 'br1'
    puuid = Column(String, unique=True, index=True)
    current_rank = Column(String)  # Validado vía Riot
    is_verified = Column(Boolean, default=False)

    user = relationship("User", back_populates="player_accounts")

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    token = Column(String, unique=True, index=True)
    # CORRECCIÓN AQUÍ: Debe ser una definición de columna
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False)

    user = relationship("User", back_populates="refresh_tokens")