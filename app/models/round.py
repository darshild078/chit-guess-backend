from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Enum as SQLEnum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.constants import RoundStatus
from app.models.base import Base
from app.utils.cuid import generate_cuid

class GameRound(Base):
    __tablename__ = "GameRound"

    id = Column(String, primary_key=True, default=generate_cuid)
    roomId = Column(String, ForeignKey("Room.id", ondelete="CASCADE"), nullable=False, index=True)
    roundNumber = Column(Integer, nullable=False)
    status = Column(SQLEnum(RoundStatus, name="RoundStatus", values_callable=lambda x: [e.value for e in x]), default=RoundStatus.waiting, nullable=False)
    aliasEpoch = Column(Integer, default=0, nullable=False)
    identitiesRevealed = Column(Boolean, default=False, nullable=False)
    
    # Mode-specific round parameters
    prompt = Column(String, nullable=True)
    secretTopic = Column(String, nullable=True)
    secretWord = Column(String, nullable=True)
    chameleonParticipantId = Column(String, nullable=True)
    wordChoices = Column(String, nullable=True) # Comma-separated or JSON list of 4 choices
    chameleonEscaped = Column(Boolean, default=False, nullable=True)
    chameleonGuessedWord = Column(Boolean, default=False, nullable=True)

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
