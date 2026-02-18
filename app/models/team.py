import uuid
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class Team(Base):
    __tablename__ = "teams"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, index=True)
    logo_url = Column(String, nullable=True)
    captain_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    members = relationship("TeamMember", back_populates="team")


class TeamMember(Base):
    __tablename__ = "team_members"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), primary_key=True)
    status = Column(String, default="pending")  # pending, accepted

    user = relationship("User", back_populates="memberships")
    team = relationship("Team", back_populates="members")