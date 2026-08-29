from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import Base
from app.utils.cuid import generate_cuid

class RoundGuess(Base):
    __tablename__ = "RoundGuess"

    id = Column(String, primary_key=True, default=generate_cuid)
    roomId = Column(String, ForeignKey("Room.id", ondelete="CASCADE"), nullable=False, index=True)
    roundId = Column(String, ForeignKey("GameRound.id", ondelete="CASCADE"), nullable=False, index=True)
    guesserId = Column(String, ForeignKey("Participant.id", ondelete="CASCADE"), nullable=False, index=True)
    chitId = Column(String, nullable=True, index=True) # nullable for chameleon votes
    guessedSenderId = Column(String, ForeignKey("Participant.id", ondelete="CASCADE"), nullable=False)
    isCorrect = Column(Boolean, default=False, nullable=False)
    isDoubleDown = Column(Boolean, default=False, nullable=False) # Double Down 2x wager
    createdAt = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    guesser = relationship("Participant", foreign_keys=[guesserId])
    guessedSender = relationship("Participant", foreign_keys=[guessedSenderId])
    round = relationship("GameRound")

    __table_args__ = (
        UniqueConstraint("roundId", "guesserId", "guessedSenderId", name="RoundGuess_roundId_guesserId_guessedSenderId_key"),
    )
