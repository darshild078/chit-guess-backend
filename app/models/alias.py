from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import Base
from app.utils.cuid import generate_cuid

class RoundAlias(Base):
    __tablename__ = "RoundAlias"

    id = Column(String, primary_key=True, default=generate_cuid)
    roundId = Column(String, ForeignKey("GameRound.id", ondelete="CASCADE"), nullable=False)
    aliasEpoch = Column(Integer, nullable=False)
    participantId = Column(String, nullable=False)
    aliasNumber = Column(Integer, nullable=False)
    opaqueAliasId = Column(String, unique=True, nullable=False, index=True)
    createdAt = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    round = relationship("GameRound", back_populates="aliasMappings")

    __table_args__ = (
        UniqueConstraint("roundId", "aliasEpoch", "participantId", name="RoundAlias_roundId_aliasEpoch_participantId_key"),
        UniqueConstraint("roundId", "aliasEpoch", "aliasNumber", name="RoundAlias_roundId_aliasEpoch_aliasNumber_key"),
    )
