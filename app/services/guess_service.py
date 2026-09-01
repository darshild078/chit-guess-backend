from collections import Counter
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, func, select

from app.core.constants import (
    GameMode,
    RoomStatus,
    RoundStatus,
    SCORE_CHAMELEON_ESCAPE,
    SCORE_CHAMELEON_STEAL,
    SCORE_CORRECT_GUESS,
    SCORE_DOUBLE_DOWN_LOSS,
    SCORE_DOUBLE_DOWN_WIN,
    SCORE_ROAST_TOP_BONUS,
    SCORE_ROAST_VOTE,
    SCORE_STEALTH_BONUS,
)
from app.core.exceptions import BadRequestException, NotFoundException
from app.core.logging import log_event
from app.models.chit import ChitMessage
from app.models.guess import RoundGuess
from app.models.participant import Participant
from app.models.room import Room
from app.models.round import GameRound
from app.schemas.guess import (
    ChameleonGuessResponseDTO,
    ChitGuessItem,
    GuessSummaryItem,
    PlayerBadgeDTO,
    RoundResultsDTO,
    RoundRevealDetailDTO,
    RoundWordDTO,
    SubmitGuessesResponseDTO,
)
from app.schemas.participant import LeaderboardItemDTO
from app.sockets.emitters import (
    emit_game_completed,
    emit_player_activity_updated,
    emit_round_revealed,
)
from app.utils.cuid import generate_cuid

async def get_round_words(
    db: AsyncSession,
    participant_id: str,
    room_id: str,
) -> List[RoundWordDTO]:
    stmt_round = (
        select(GameRound)
        .where(GameRound.roomId == room_id)
        .order_by(GameRound.roundNumber.desc())
    )
    res_round = await db.execute(stmt_round)
    current_round = res_round.scalars().first()

    if not current_round:
        return []

    stmt_room = select(Room).where(Room.id == room_id)
    res_room = await db.execute(stmt_room)
    room = res_room.scalars().first()
    game_mode = room.gameMode if room else GameMode.confessions.value

    stmt_chits = select(ChitMessage).where(ChitMessage.roundId == current_round.id)
    res_chits = await db.execute(stmt_chits)
    chits = list(res_chits.scalars().all())

    stmt_p = select(Participant).where(Participant.roomId == room_id)
    res_p = await db.execute(stmt_p)
    participants = {p.id: p.displayName for p in res_p.scalars().all()}

    return [
        RoundWordDTO(
            chitId=c.id,
            body=c.body,
            isOwnWord=(c.senderId == participant_id),
            authorDisplayName=participants.get(c.senderId) if game_mode == GameMode.chameleon.value else None,
        )
        for c in chits
    ]

async def submit_guesses(
    db: AsyncSession,
    participant_id: str,
    room_id: str,
    guesses: List[ChitGuessItem],
) -> SubmitGuessesResponseDTO:
    stmt_round = (
        select(GameRound)
        .where(GameRound.roomId == room_id)
        .order_by(GameRound.roundNumber.desc())
    )
    res_round = await db.execute(stmt_round)
    current_round = res_round.scalars().first()

    if not current_round or current_round.status != RoundStatus.guessing:
        raise BadRequestException("Guessing is not open for this round.")

    stmt_del = delete(RoundGuess).where(
        RoundGuess.roundId == current_round.id,
        RoundGuess.guesserId == participant_id,
    )
    await db.execute(stmt_del)

    for g in guesses:
        guess_record = RoundGuess(
            id=generate_cuid(),
            roomId=room_id,
            roundId=current_round.id,
            guesserId=participant_id,
            chitId=g.chitId,
            guessedSenderId=g.guessedParticipantId,
            isCorrect=False,
            isDoubleDown=bool(g.isDoubleDown),
        )
        db.add(guess_record)

    await db.flush()

    log_event(
        action="submit_guesses",
        status="success",
        room_id=room_id,
        user_id=participant_id,
        message="Guesses submitted successfully",
    )

    await emit_player_activity_updated(room_id)

    # Check if all participants have submitted guesses -> auto-reveal
    all_guessed = await check_all_guesses_submitted(db, room_id)
    if all_guessed:
        results = await calculate_and_reveal_scores(db, room_id)
        if results.isFinalRound:
            await emit_game_completed(room_id, results.model_dump(mode="json"))
        else:
            await emit_round_revealed(room_id, results.model_dump(mode="json"))

    return SubmitGuessesResponseDTO(lockedIn=True)

async def submit_chameleon_word_guess(
    db: AsyncSession,
    participant_id: str,
    room_id: str,
    guessed_word: str,
) -> ChameleonGuessResponseDTO:
    stmt_round = (
        select(GameRound)
        .where(GameRound.roomId == room_id)
        .order_by(GameRound.roundNumber.desc())
    )
    res_round = await db.execute(stmt_round)
    current_round = res_round.scalars().first()

    if not current_round:
        raise NotFoundException("No active round.")

    if current_round.chameleonParticipantId != participant_id:
        raise BadRequestException("Only the Chameleon can make a Last Stand word guess.")

    is_correct = bool(current_round.secretWord and current_round.secretWord.strip().lower() == guessed_word.strip().lower())
    current_round.chameleonGuessedWord = is_correct

    if is_correct:
        stmt_p = select(Participant).where(Participant.id == participant_id)
        res_p = await db.execute(stmt_p)
        cham = res_p.scalars().first()
        if cham:
            cham.score += SCORE_CHAMELEON_STEAL
            db.add(cham)

    db.add(current_round)
    await db.flush()

    results = await calculate_and_reveal_scores(db, room_id)
    if results.isFinalRound:
        await emit_game_completed(room_id, results.model_dump(mode="json"))
    else:
        await emit_round_revealed(room_id, results.model_dump(mode="json"))

    return ChameleonGuessResponseDTO(isCorrect=is_correct)

async def check_all_guesses_submitted(db: AsyncSession, room_id: str) -> bool:
    stmt_round = (
        select(GameRound)
        .where(GameRound.roomId == room_id)
        .order_by(GameRound.roundNumber.desc())
    )
    res_round = await db.execute(stmt_round)
    current_round = res_round.scalars().first()

    if not current_round or current_round.status != RoundStatus.guessing:
        return False

    stmt_active = select(func.count()).select_from(Participant).where(
        Participant.roomId == room_id,
        Participant.removed == False,
        Participant.connected == True,
    )
    res_active = await db.execute(stmt_active)
    total_active = res_active.scalar() or 0

    if total_active <= 1:
        return True

    stmt_guessers = select(func.count(func.distinct(RoundGuess.guesserId))).where(
        RoundGuess.roundId == current_round.id
    )
    res_guessers = await db.execute(stmt_guessers)
    guessers_count = res_guessers.scalar() or 0

    return guessers_count >= total_active

async def calculate_and_reveal_scores(db: AsyncSession, room_id: str) -> RoundResultsDTO:
    stmt_round = (
        select(GameRound)
        .where(GameRound.roomId == room_id)
        .order_by(GameRound.roundNumber.desc())
    )
    res_round = await db.execute(stmt_round)
    current_round = res_round.scalars().first()

    if not current_round:
        raise NotFoundException("No active round found to calculate scores.")

    stmt_room = select(Room).where(Room.id == room_id)
    res_room = await db.execute(stmt_room)
    room = res_room.scalars().first()
    game_mode = room.gameMode if room else GameMode.confessions.value

    stmt_p = select(Participant).where(Participant.roomId == room_id)
    res_p = await db.execute(stmt_p)
    participants = list(res_p.scalars().all())
    participant_map = {p.id: p for p in participants}

    stmt_chits = select(ChitMessage).where(ChitMessage.roundId == current_round.id)
    res_chits = await db.execute(stmt_chits)
    chits = list(res_chits.scalars().all())
    chit_author_map = {c.id: c.senderId for c in chits}

    stmt_guesses = select(RoundGuess).where(RoundGuess.roundId == current_round.id)
    res_guesses = await db.execute(stmt_guesses)
    guesses = list(res_guesses.scalars().all())

    chameleon_caught = False
    chameleon_escaped = False

    if not current_round.identitiesRevealed:
        # MODE 1: SECRET CONFESSIONS
        if game_mode == GameMode.confessions.value:
            guesses_per_author = Counter()

            for g in guesses:
                real_author_id = chit_author_map.get(g.chitId)
                if real_author_id:
                    if g.guessedSenderId == real_author_id:
                        g.isCorrect = True
                        guesses_per_author[real_author_id] += 1
                        guesser = participant_map.get(g.guesserId)
                        if guesser:
                            pts = SCORE_DOUBLE_DOWN_WIN if g.isDoubleDown else SCORE_CORRECT_GUESS
                            guesser.score += pts
                            db.add(guesser)
                    else:
                        g.isCorrect = False
                        if g.isDoubleDown:
                            guesser = participant_map.get(g.guesserId)
                            if guesser:
                                guesser.score = max(0, guesser.score - SCORE_DOUBLE_DOWN_LOSS)
                                db.add(guesser)
                db.add(g)

            # Stealth Bonus (+150 pts if 0 people guessed you)
            for c in chits:
                if guesses_per_author[c.senderId] == 0:
                    author = participant_map.get(c.senderId)
                    if author and len(participants) > 1:
                        author.score += SCORE_STEALTH_BONUS
                        db.add(author)

        # MODE 2: THE CHAMELEON
        elif game_mode == GameMode.chameleon.value:
            cham_id = current_round.chameleonParticipantId
            vote_counts = Counter()

            for g in guesses:
                vote_counts[g.guessedSenderId] += 1

            most_voted_id = None
            highest_votes = 0
            if vote_counts:
                most_voted_id, highest_votes = vote_counts.most_common(1)[0]

            if most_voted_id == cham_id and highest_votes > 0:
                chameleon_caught = True
                for g in guesses:
                    if g.guessedSenderId == cham_id:
                        g.isCorrect = True
                        guesser = participant_map.get(g.guesserId)
                        if guesser:
                            pts = SCORE_DOUBLE_DOWN_WIN if g.isDoubleDown else SCORE_CORRECT_GUESS
                            guesser.score += pts
                            db.add(guesser)
                    db.add(g)
            else:
                chameleon_escaped = True
                cham_player = participant_map.get(cham_id)
                if cham_player:
                    cham_player.score += SCORE_CHAMELEON_ESCAPE
                    db.add(cham_player)

            current_round.chameleonEscaped = chameleon_escaped

        # MODE 3: FRIEND ROASTS
        elif game_mode == GameMode.roasts.value:
            votes_per_author = Counter()

            for g in guesses:
                votes_per_author[g.guessedSenderId] += 1

            for author_id, vote_cnt in votes_per_author.items():
                author = participant_map.get(author_id)
                if author:
                    author.score += (vote_cnt * SCORE_ROAST_VOTE)
                    db.add(author)

            if votes_per_author:
                top_author_id, _ = votes_per_author.most_common(1)[0]
                top_author = participant_map.get(top_author_id)
                if top_author:
                    top_author.score += SCORE_ROAST_TOP_BONUS
                    db.add(top_author)

        current_round.identitiesRevealed = True
        current_round.status = RoundStatus.revealed
        db.add(current_round)

        if room:
            if room.currentRoundNumber >= room.totalRounds:
                room.status = RoomStatus.completed
            else:
                room.status = RoomStatus.revealed
            db.add(room)

        await db.flush()

    chits_detail: List[RoundRevealDetailDTO] = []
    for c in chits:
        author = participant_map.get(c.senderId)
        author_name = author.displayName if author else "Unknown"

        correct_guesser_names = []
        guesses_summary = []
        votes_count = 0

        for g in guesses:
            if g.chitId == c.id or (game_mode == GameMode.roasts.value and g.guessedSenderId == c.senderId):
                guesser = participant_map.get(g.guesserId)
                guessed_player = participant_map.get(g.guessedSenderId)
                guesser_name = guesser.displayName if guesser else "Player"
                guessed_name = guessed_player.displayName if guessed_player else "Player"

                is_corr = (g.guessedSenderId == c.senderId)
                if is_corr:
                    correct_guesser_names.append(guesser_name)
                if g.guessedSenderId == c.senderId:
                    votes_count += 1

                guesses_summary.append(
                    GuessSummaryItem(
                        guesserName=guesser_name,
                        guessedPlayerName=guessed_name,
                        isCorrect=is_corr,
                        isDoubleDown=bool(g.isDoubleDown),
                    )
                )

        chits_detail.append(
            RoundRevealDetailDTO(
                chitId=c.id,
                body=c.body,
                authorParticipantId=c.senderId,
                authorDisplayName=author_name,
                correctGuessers=correct_guesser_names,
                guessesSummary=guesses_summary,
                stealthBonusAwarded=(len(correct_guesser_names) == 0 and len(participants) > 1),
                votesCount=votes_count,
            )
        )

    leaderboard = await get_leaderboard(db, room_id)
    is_final = bool(room and current_round.roundNumber >= room.totalRounds)

    awards: List[PlayerBadgeDTO] = []
    if is_final and len(leaderboard) > 0:
        awards = await generate_awards(db, room_id, leaderboard)

    cham_author = participant_map.get(current_round.chameleonParticipantId)
    cham_name = cham_author.displayName if cham_author else None

    return RoundResultsDTO(
        roundNumber=current_round.roundNumber,
        totalRounds=room.totalRounds if room else 3,
        isFinalRound=is_final,
        gameMode=game_mode,
        prompt=current_round.prompt,
        secretTopic=current_round.secretTopic,
        secretWord=current_round.secretWord,
        chameleonParticipantId=current_round.chameleonParticipantId,
        chameleonDisplayName=cham_name,
        chameleonCaught=chameleon_caught,
        chameleonEscaped=current_round.chameleonEscaped,
        chameleonGuessedWord=current_round.chameleonGuessedWord,
        chits=chits_detail,
        leaderboard=leaderboard,
        awards=awards,
    )

async def generate_awards(
    db: AsyncSession, room_id: str, leaderboard: List[LeaderboardItemDTO]
) -> List[PlayerBadgeDTO]:
    badges: List[PlayerBadgeDTO] = []
    if not leaderboard:
        return badges

    top_player = leaderboard[0]
    badges.append(
        PlayerBadgeDTO(
            badgeId="mind_reader",
            title="The Mind Reader",
            emoji="🧠",
            description="Highest overall score and deduction mastery!",
            recipientDisplayName=top_player.displayName,
            recipientParticipantId=top_player.participantId,
        )
    )

    if len(leaderboard) >= 2:
        runner_up = leaderboard[1]
        badges.append(
            PlayerBadgeDTO(
                badgeId="puppet_master",
                title="The Puppet Master",
                emoji="🎭",
                description="Fooled the room and bluffed like a champion!",
                recipientDisplayName=runner_up.displayName,
                recipientParticipantId=runner_up.participantId,
            )
        )

    if len(leaderboard) >= 3:
        third = leaderboard[-1]
        badges.append(
            PlayerBadgeDTO(
                badgeId="chaos_agent",
                title="The Chaos Agent",
                emoji="💣",
                description="Created absolute mayhem and kept everyone guessing!",
                recipientDisplayName=third.displayName,
                recipientParticipantId=third.participantId,
            )
        )

    return badges

async def get_leaderboard(db: AsyncSession, room_id: str) -> List[LeaderboardItemDTO]:
    stmt = (
        select(Participant)
        .where(
            Participant.roomId == room_id,
            Participant.removed == False,
        )
        .order_by(Participant.score.desc(), Participant.joinedAt.asc())
    )
    res = await db.execute(stmt)
    players = list(res.scalars().all())

    leaderboard = []
    for rank, p in enumerate(players, start=1):
        leaderboard.append(
            LeaderboardItemDTO(
                participantId=p.id,
                displayName=p.displayName,
                score=p.score,
                rank=rank,
                connected=p.connected,
                role=p.role.value,
            )
        )
    return leaderboard


