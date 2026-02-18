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
    # Estos deben ser nullable=True para que el login inicial no falle
    internal_nick = Column(String, unique=True, index=True, nullable=True)
    whatsapp = Column(String, nullable=True)
    country = Column(String, nullable=True)
    role = Column(Enum(UserRole), default=UserRole.PLAYER)

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