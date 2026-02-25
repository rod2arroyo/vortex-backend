import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, ForeignKey, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base

class InvitationStatus(enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


class TeamInvitation(Base):
    __tablename__ = "team_invitations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    inviter_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)  # Quién invitó (Capitán)

    # Si es invitación directa, guardamos el ID del usuario.
    # Si es por Link, esto puede quedar NULL hasta que alguien lo use.
    invitee_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    token = Column(String, unique=True, index=True, nullable=False)  # Para el link y validación
    status = Column(Enum(InvitationStatus), default=InvitationStatus.PENDING)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True))

    team = relationship("Team")
    inviter = relationship("User", foreign_keys=[inviter_id])
    invitee = relationship("User", foreign_keys=[invitee_id])