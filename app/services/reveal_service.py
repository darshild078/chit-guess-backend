from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.constants import RoomStatus, RoundStatus
from app.core.exceptions import NotFoundException
from app.models.chit import ChitMessage
from app.models.participant import Participant
from app.models.room import Room
from app.models.round import GameRound
from app.schemas.reveal import RevealedChitDTO, RevealResultsDTO

async def reveal_identities(db: AsyncSession, room_id: str) -> RevealResultsDTO:
    stmt_round = (
        select(GameRound)
        .where(GameRound.roomId == room_id)
        .order_by(GameRound.roundNumber.desc())
    )
    res_round = await db.execute(stmt_round)
    current_round = res_round.scalars().first()

    if not current_round:
        raise NotFoundException("No active round found to reveal.")

    now = datetime.now(timezone.utc)
    current_round.status = RoundStatus.revealed
    current_round.identitiesRevealed = True
    current_round.revealedAt = now
    db.add(current_round)

    stmt_room = select(Room).where(Room.id == room_id)
    res_room = await db.execute(stmt_room)
    room = res_room.scalars().first()
    if room:
        room.status = RoomStatus.revealed
        db.add(room)

    await db.flush()
    return await get_revealed_results(db, room_id)

async def get_revealed_results(db: AsyncSession, room_id: str) -> RevealResultsDTO:
    stmt_round = (
        select(GameRound)
        .where(GameRound.roomId == room_id)
        .order_by(GameRound.roundNumber.desc())
    )
    res_round = await db.execute(stmt_round)
    current_round = res_round.scalars().first()

    if not current_round:
        return RevealResultsDTO(roundNumber=0, chits=[])

    stmt_p = select(Participant).where(Participant.roomId == room_id)
    res_p = await db.execute(stmt_p)
    participants = list(res_p.scalars().all())
    name_map = {p.id: p.displayName for p in participants}

    stmt_chits = select(ChitMessage).where(ChitMessage.roundId == current_round.id)
    res_chits = await db.execute(stmt_chits)
    chits = list(res_chits.scalars().all())

    revealed_list = []
    for chit in chits:
        sender_name = name_map.get(chit.senderId, "Unknown")
        guessed_name = name_map.get(chit.guessedParticipantId) if chit.guessedParticipantId else None
        was_correct = (chit.guessedParticipantId == chit.senderId) if chit.guessedParticipantId else None

        revealed_list.append(
            RevealedChitDTO(
                chitId=chit.id,
                senderDisplayName=sender_name,
                body=chit.body,
                submittedAt=chit.submittedAt,
                guessedDisplayName=guessed_name,
                wasCorrect=was_correct,
            )
        )

    return RevealResultsDTO(
        roundNumber=current_round.roundNumber,
        chits=revealed_list,
    )


