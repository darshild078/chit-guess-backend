from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.exceptions import NotFoundException
from app.models.chit import ChitMessage
from app.models.round import GameRound
from app.schemas.inbox import (
    AnonymousChitDTO,
    AnonymousInboxDTO,
    MarkChitGuessedDTO,
    MarkChitReadDTO,
)
from app.services.alias_service import (
    get_or_create_aliases_for_epoch,
    resolve_opaque_alias_id,
)

async def get_anonymous_inbox(db: AsyncSession, room_id: str) -> AnonymousInboxDTO:
    stmt_round = (
        select(GameRound)
        .where(GameRound.roomId == room_id)
        .order_by(GameRound.roundNumber.desc())
    )
    res_round = await db.execute(stmt_round)
    current_round = res_round.scalars().first()

    if not current_round:
        return AnonymousInboxDTO(roundNumber=0, aliasEpoch=0, chits=[])

    aliases = await get_or_create_aliases_for_epoch(db, current_round)
    alias_map = {a.participantId: a for a in aliases}

    stmt_chits = select(ChitMessage).where(ChitMessage.roundId == current_round.id)
    res_chits = await db.execute(stmt_chits)
    chits = list(res_chits.scalars().all())

    dto_list = []
    for chit in chits:
        alias = alias_map.get(chit.senderId)
        alias_number = alias.aliasNumber if alias else 0
        opaque_id = alias.opaqueAliasId if alias else chit.id

        dto_list.append(
            AnonymousChitDTO(
                anonymousChitId=opaque_id,
                alias=f"Player {alias_number}",
                body=chit.body,
                submittedAt=chit.submittedAt,
                isRead=chit.isRead,
                isGuessed=chit.isGuessed,
            )
        )

    dto_list.sort(key=lambda x: int(x.alias.split(" ")[1]) if " " in x.alias else 0)

    return AnonymousInboxDTO(
        roundNumber=current_round.roundNumber,
        aliasEpoch=current_round.aliasEpoch,
        chits=dto_list,
    )

async def mark_chit_read(
    db: AsyncSession,
    room_id: str,
    opaque_alias_id: str,
    is_read: bool,
) -> MarkChitReadDTO:
    alias = await resolve_opaque_alias_id(db, opaque_alias_id)
    sender_id = alias.participantId if alias else opaque_alias_id

    stmt_round = (
        select(GameRound)
        .where(GameRound.roomId == room_id)
        .order_by(GameRound.roundNumber.desc())
    )
    res_round = await db.execute(stmt_round)
    current_round = res_round.scalars().first()

    if not current_round:
        raise NotFoundException("Round not found.")

    stmt_chit = select(ChitMessage).where(
        ChitMessage.roundId == current_round.id,
        ChitMessage.senderId == sender_id,
    )
    res_chit = await db.execute(stmt_chit)
    chit = res_chit.scalars().first()

    if chit:
        chit.isRead = is_read
        db.add(chit)
        await db.flush()

    return MarkChitReadDTO(isRead=is_read)

async def mark_chit_guessed(
    db: AsyncSession,
    room_id: str,
    opaque_alias_id: str,
    is_guessed: bool,
    guessed_alias_id: Optional[str] = None,
) -> MarkChitGuessedDTO:
    alias = await resolve_opaque_alias_id(db, opaque_alias_id)
    sender_id = alias.participantId if alias else opaque_alias_id

    stmt_round = (
        select(GameRound)
        .where(GameRound.roomId == room_id)
        .order_by(GameRound.roundNumber.desc())
    )
    res_round = await db.execute(stmt_round)
    current_round = res_round.scalars().first()

    if not current_round:
        raise NotFoundException("Round not found.")

    stmt_chit = select(ChitMessage).where(
        ChitMessage.roundId == current_round.id,
        ChitMessage.senderId == sender_id,
    )
    res_chit = await db.execute(stmt_chit)
    chit = res_chit.scalars().first()

    if chit:
        chit.isGuessed = is_guessed
        if guessed_alias_id:
            target_alias = await resolve_opaque_alias_id(db, guessed_alias_id)
            chit.guessedParticipantId = target_alias.participantId if target_alias else guessed_alias_id
        db.add(chit)
        await db.flush()

    return MarkChitGuessedDTO(isGuessed=is_guessed)


