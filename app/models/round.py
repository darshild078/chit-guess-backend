from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Enum as SQLEnum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import Base
from app.models.enums import RoundStatus
from app.utils.cuid import generate_cuid

class GameRound(Base):
    __tablename__ = "GameRound"

    id = Column(String, primary_key=True, default=generate_cuid)
    roomId = Column(String, ForeignKey("Room.id", ondelete="CASCADE"), nullable=False, index=True)
    roundNumber = Column(Integer, nullable=False)
    status = Column(SQLEnum(RoundStatus, name="RoundStatus", values_callable=lambda x: [e.value for e in x]), default=RoundStatus.waiting, nullable=False)
    aliasEpoch = Column(Integer, default=0, nullable=False)
    identitiesRevealed = Column(Boolean, default=False, nullable=False)
    submissionsOpenedAt = Column(DateTime(timezone=True), nullable=True)
    submissionsClosedAt = Column(DateTime(timezone=True), nullable=True)
    revealedAt = Column(DateTime(timezone=True), nullable=True)
    completedAt = Column(DateTime(timezone=True), nullable=True)
    createdAt = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    room = relationship("Room", back_populates="rounds")
    chits = relationship("ChitMessage", back_populates="round", cascade="all, delete-orphan")
    aliasMappings = relationship("RoundAlias", back_populates="round", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("roomId", "roundNumber", name="GameRound_roomId_roundNumber_key"),
    )
