from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.constants import RoundStatus
from app.core.exceptions import BadRequestException, NotFoundException
from app.core.logging import log_event
from app.models.chit import ChitMessage
from app.models.round import GameRound
from app.schemas.submission import DeleteChitDTO, MySubmissionDTO, SubmissionStatusDTO
from app.services.round_service import advance_to_guessing, check_all_submissions_done
from app.sockets.emitters import (
    emit_guessing_started,
    emit_player_activity_updated,
    emit_submission_status,
)
from app.utils.cuid import generate_cuid
from app.utils.sanitize import sanitize_single_word

async def get_my_submission(
    db: AsyncSession,
    participant_id: str,
    room_id: str,
) -> Optional[MySubmissionDTO]:
    stmt_round = (
        select(GameRound)
        .where(GameRound.roomId == room_id)
        .order_by(GameRound.roundNumber.desc())
    )
    res_round = await db.execute(stmt_round)
    current_round = res_round.scalars().first()

    if not current_round:
        return None

    stmt_chit = select(ChitMessage).where(
        ChitMessage.roundId == current_round.id,
        ChitMessage.senderId == participant_id,
    )
    res_chit = await db.execute(stmt_chit)
    chit = res_chit.scalars().first()

    if not chit:
        return None

    return MySubmissionDTO(
        body=chit.body,
        submittedAt=chit.submittedAt,
        updatedAt=chit.updatedAt,
    )

async def get_submission_status(
    db: AsyncSession,
    participant_id: str,
    room_id: str,
) -> SubmissionStatusDTO:
    stmt_round = (
        select(GameRound)
        .where(GameRound.roomId == room_id)
        .order_by(GameRound.roundNumber.desc())
    )
    res_round = await db.execute(stmt_round)
    current_round = res_round.scalars().first()

    if not current_round:
        return SubmissionStatusDTO(hasSubmitted=False, canEdit=False, canDelete=False, canSubmit=False)

    is_open = current_round.status == RoundStatus.submissions_open

    stmt_chit = select(ChitMessage).where(
        ChitMessage.roundId == current_round.id,
        ChitMessage.senderId == participant_id,
    )
    res_chit = await db.execute(stmt_chit)
    chit = res_chit.scalars().first()

    has_submitted = (chit is not None)

    return SubmissionStatusDTO(
        hasSubmitted=has_submitted,
        canEdit=(has_submitted and is_open),
        canDelete=(has_submitted and is_open),
        canSubmit=(not has_submitted and is_open),
    )

async def submit_chit(
    db: AsyncSession,
    participant_id: str,
    room_id: str,
    body: str,
) -> MySubmissionDTO:
    clean_word = sanitize_single_word(body)

    stmt_round = (
        select(GameRound)
        .where(GameRound.roomId == room_id)
        .order_by(GameRound.roundNumber.desc())
    )
    res_round = await db.execute(stmt_round)
    current_round = res_round.scalars().first()

    if not current_round or current_round.status != RoundStatus.submissions_open:
        raise BadRequestException("Submissions are currently closed. The round has already progressed.")

    stmt_chit = select(ChitMessage).where(
        ChitMessage.roundId == current_round.id,
        ChitMessage.senderId == participant_id,
    )
    res_chit = await db.execute(stmt_chit)
    existing = res_chit.scalars().first()

    now = datetime.now(timezone.utc)
    if existing:
        existing.body = clean_word
        existing.updatedAt = now
        db.add(existing)
        await db.flush()
        result_dto = MySubmissionDTO(body=existing.body, submittedAt=existing.submittedAt, updatedAt=existing.updatedAt)
    else:
        new_chit = ChitMessage(
            id=generate_cuid(),
            roomId=room_id,
            roundId=current_round.id,
            senderId=participant_id,
            body=clean_word,
            isRead=False,
            isGuessed=False,
            submittedAt=now,
            updatedAt=now,
        )
        db.add(new_chit)
        await db.flush()
        result_dto = MySubmissionDTO(body=new_chit.body, submittedAt=new_chit.submittedAt, updatedAt=new_chit.updatedAt)

    log_event(
        action="submit_chit",
        status="success",
        room_id=room_id,
        user_id=participant_id,
        message="Chit submitted successfully",
    )

    await emit_player_activity_updated(room_id)
    await emit_submission_status(participant_id, {
        "hasSubmitted": True,
        "canEdit": True,
        "canDelete": True,
        "canSubmit": False,
    })

    # Check if all participants have submitted -> auto-advance to Guessing phase
    all_submitted = await check_all_submissions_done(db, room_id)
    if all_submitted:
        await advance_to_guessing(db, room_id)
        await emit_guessing_started(room_id)

    return result_dto

async def edit_chit(
    db: AsyncSession,
    participant_id: str,
    room_id: str,
    body: str,
) -> MySubmissionDTO:
    clean_word = sanitize_single_word(body)

    stmt_round = (
        select(GameRound)
        .where(GameRound.roomId == room_id)
        .order_by(GameRound.roundNumber.desc())
    )
    res_round = await db.execute(stmt_round)
    current_round = res_round.scalars().first()

    if not current_round or current_round.status != RoundStatus.submissions_open:
        raise BadRequestException("Submissions are closed. Cannot modify secret word.")

    stmt_chit = select(ChitMessage).where(
        ChitMessage.roundId == current_round.id,
        ChitMessage.senderId == participant_id,
    )
    res_chit = await db.execute(stmt_chit)
    chit = res_chit.scalars().first()

    if not chit:
        raise NotFoundException("No submission found to edit.")

    now = datetime.now(timezone.utc)
    chit.body = clean_word
    chit.updatedAt = now
    db.add(chit)
    await db.flush()

    await emit_player_activity_updated(room_id)

    return MySubmissionDTO(body=chit.body, submittedAt=chit.submittedAt, updatedAt=chit.updatedAt)

async def delete_chit(
    db: AsyncSession,
    participant_id: str,
    room_id: str,
) -> DeleteChitDTO:
    stmt_round = (
        select(GameRound)
        .where(GameRound.roomId == room_id)
        .order_by(GameRound.roundNumber.desc())
    )
    res_round = await db.execute(stmt_round)
    current_round = res_round.scalars().first()

    if not current_round or current_round.status != RoundStatus.submissions_open:
        raise BadRequestException("Submissions are closed. Cannot delete secret word.")

    stmt_chit = select(ChitMessage).where(
        ChitMessage.roundId == current_round.id,
        ChitMessage.senderId == participant_id,
    )
    res_chit = await db.execute(stmt_chit)
    chit = res_chit.scalars().first()

    if chit:
        await db.delete(chit)
        await db.flush()

    await emit_player_activity_updated(room_id)
    await emit_submission_status(participant_id, {
        "hasSubmitted": False,
        "canEdit": False,
        "canDelete": False,
        "canSubmit": True,
    })

    return DeleteChitDTO(deleted=True)


