from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Enum as SQLEnum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.constants import ParticipantRole
from app.models.base import Base
from app.utils.cuid import generate_cuid

class Participant(Base):
    __tablename__ = "Participant"

    id = Column(String, primary_key=True, default=generate_cuid)
    roomId = Column(String, ForeignKey("Room.id", ondelete="CASCADE"), nullable=False, index=True)
    displayName = Column(String, nullable=False)
    role = Column(SQLEnum(ParticipantRole, name="ParticipantRole", values_callable=lambda x: [e.value for e in x]), nullable=False)
    score = Column(Integer, default=0, nullable=False)
    connected = Column(Boolean, default=False, nullable=False)
    removed = Column(Boolean, default=False, nullable=False)
    sessionVersion = Column(Integer, default=1, nullable=False)
    joinedAt = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    lastSeenAt = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    room = relationship("Room", back_populates="participants")
    chits = relationship("ChitMessage", back_populates="sender", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("roomId", "displayName", name="Participant_roomId_displayName_key"),
    )
