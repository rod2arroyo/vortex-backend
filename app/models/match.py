import uuid
import enum
from sqlalchemy import Column, String, ForeignKey, DateTime, Boolean, Integer, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base


class SchedulingType(str, enum.Enum):
    FIXED = "fixed"  # Horario inamovible definido por admin
    NEGOTIATED = "negotiated"  # Ventana de negociación entre capitanes


class MatchStatus(str, enum.Enum):
    WAITING_TEAMS = "waiting_teams"  # Esperando que terminen partidos previos
    PENDING_CONFIRMATION = "pending_confirmation"  # Equipos listos, falta agendar
    SCHEDULED = "scheduled"  # Horario definido, listo para jugar
    ONGOING = "ongoing"  # Partida en curso (vía Webhook)
    FINISHED = "finished"
    DISPUTED = "disputed"  # Conflicto reportado


class Match(Base):
    __tablename__ = "matches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tournament_id = Column(UUID(as_uuid=True), ForeignKey("tournaments.id"))

    # --- Lógica de Bracket (Avance Automático) ---
    round_number = Column(Integer)  # Ejemplo: 1 (Ronda 1), 2 (Cuartos), 3 (Semis)
    next_match_id = Column(UUID(as_uuid=True), ForeignKey("matches.id"), nullable=True)

    # --- Participantes ---
    team_a_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=True)
    team_b_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=True)
    winner_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=True)

    # --- Configuración de la Serie ---
    # Soporta Bo1, Bo3, Bo5
    match_type = Column(String, default="BO1")
    riot_tournament_code = Column(String, unique=True, index=True)

    # --- Agendamiento y Negociación ---
    # Diferencia entre horario fijo y flexible
    scheduling_type = Column(Enum(SchedulingType), default=SchedulingType.FIXED)
    scheduled_at = Column(DateTime, nullable=True)  # Hora final acordada

    status = Column(Enum(MatchStatus), default=MatchStatus.WAITING_TEAMS)

    # Relaciones
    proposals = relationship("MatchProposal", back_populates="match")
    games = relationship("Game", back_populates="match")


class Game(Base):
    """
    Representa cada mapa individual dentro de una serie (Bo3/Bo5).
    Crucial para el rastreo de victorias acumuladas.
    """
    __tablename__ = "games"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id = Column(UUID(as_uuid=True), ForeignKey("matches.id"))
    riot_game_id = Column(String, unique=True)  # ID oficial de la partida en Riot
    winner_team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"))

    match = relationship("Match", back_populates="games")


class MatchProposal(Base):
    """Lógica para el Modelo Flexible de agendamiento"""
    __tablename__ = "match_proposals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id = Column(UUID(as_uuid=True), ForeignKey("matches.id"))
    proposer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))  # Capitán que sugiere

    # Almacena hasta 3 slots propuestos
    proposed_slots = Column(JSONB)
    is_accepted = Column(Boolean, default=False)

    match = relationship("Match", back_populates="proposals")