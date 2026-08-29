from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.models.base import Base
from app.models.enums import RoomStatus
from app.utils.cuid import generate_cuid

class Room(Base):
    __tablename__ = "Room"

    id = Column(String, primary_key=True, default=generate_cuid)
    code = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=True)
    status = Column(SQLEnum(RoomStatus, name="RoomStatus", values_callable=lambda x: [e.value for e in x]), default=RoomStatus.lobby, nullable=False)
    ownerParticipantId = Column(String, nullable=True)
    maxPlayers = Column(Integer, default=10, nullable=False)
    locked = Column(Boolean, default=False, nullable=False)
    currentRoundNumber = Column(Integer, default=0, nullable=False)
    expiresAt = Column(DateTime(timezone=True), nullable=False)
    createdAt = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updatedAt = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    participants = relationship("Participant", back_populates="room", cascade="all, delete-orphan")
    rounds = relationship("GameRound", back_populates="room", cascade="all, delete-orphan")
