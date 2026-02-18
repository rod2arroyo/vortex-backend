import enum
import uuid

from sqlalchemy import Column, UUID, String, Float, Enum, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.core.database import Base


class TournamentStatus(enum.Enum):
    WAITING = "waiting"
    ONGOING = "ongoing"
    FINISHED = "finished"


class Tournament(Base):
    __tablename__ = "tournaments"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String)
    category = Column(String)  # Low, High, Free Elo
    entry_fee = Column(Float, default=0.0)
    prize_pool = Column(Float, default=0.0)
    max_teams = Column(Integer)
    status = Column(Enum(TournamentStatus), default=TournamentStatus.WAITING)

    registrations = relationship("Registration", back_populates="tournament")


class Registration(Base):
    __tablename__ = "registrations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tournament_id = Column(UUID(as_uuid=True), ForeignKey("tournaments.id"))
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"))
    payment_status = Column(String, default="pending")  # pending, verified, rejected

    payment_proof = relationship("Payment", back_populates="registration", uselist=False)
    tournament = relationship("Tournament", back_populates="registrations")


class Payment(Base):
    __tablename__ = "payments"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    registration_id = Column(UUID(as_uuid=True), ForeignKey("registrations.id"))
    receipt_url = Column(String)
    amount = Column(Float)
    verified_at = Column(DateTime, nullable=True)
    verified_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    registration = relationship("Registration", back_populates="payment_proof")