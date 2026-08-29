from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import Base
from app.utils.cuid import generate_cuid

class ChitMessage(Base):
    __tablename__ = "ChitMessage"

    id = Column(String, primary_key=True, default=generate_cuid)
    roomId = Column(String, nullable=False, index=True)
    roundId = Column(String, ForeignKey("GameRound.id", ondelete="CASCADE"), nullable=False, index=True)
    senderId = Column(String, ForeignKey("Participant.id", ondelete="CASCADE"), nullable=False)
    body = Column(String, nullable=False)
    isRead = Column(Boolean, default=False, nullable=False)
    isGuessed = Column(Boolean, default=False, nullable=False)
    guessedParticipantId = Column(String, nullable=True)
    submittedAt = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updatedAt = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    round = relationship("GameRound", back_populates="chits")
    sender = relationship("Participant", back_populates="chits")

    __table_args__ = (
        UniqueConstraint("roundId", "senderId", name="ChitMessage_roundId_senderId_key"),
    )
