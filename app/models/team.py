from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class Team(Base):
    """Modelo para representar los equipos en Vortex."""
    __tablename__ = "teams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, index=True, nullable=False)

    # Nuevo: Tag de 3 a 5 caracteres (limitamos a 5 en la BD)
    tag = Column(String(5), unique=True, index=True, nullable=False)

    # Nuevo: Descripción del equipo
    description = Column(Text, nullable=True)

    # Modificado: Preparado para S3, inicia en null por defecto
    logo_url = Column(String, nullable=True, default=None)

    # El creador es el Capitán (Dueño del equipo)
    captain_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relaciones
    captain = relationship("User")
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")


class TeamMember(Base):
    """Relación entre jugadores y equipos para torneos."""
    __tablename__ = "team_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    joined_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    team = relationship("Team", back_populates="members")
    user = relationship("User", back_populates="memberships")

    @property
    def riot_id_full(self) -> str | None:
        """Devuelve 'Faker#T1' si tiene cuenta vinculada"""
        if self.user and self.user.player_accounts:
            account = self.user.player_accounts[0]
            return f"{account.riot_id}#{account.riot_tag}"
        return None  # O "No vinculado"

    @property
    def player_name(self) -> str | None:
        """Devuelve el Nick Interno de Vortex (el nombre de la página)"""
        if self.user:
            return self.user.internal_nick
        return "Usuario Desconocido"