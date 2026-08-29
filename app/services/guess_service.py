from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from app.models.chit import ChitMessage
from app.models.round import GameRound
from app.models.room import Room
from app.models.participant import Participant
from app.models.guess import RoundGuess
from app.models.enums import RoomStatus, RoundStatus
from app.schemas.guess import (
    RoundWordDTO,
    ChitGuessItem,
    RoundResultsDTO,
    RoundRevealDetailDTO,
    GuessSummaryItem,
)
from app.schemas.participant import LeaderboardItemDTO
from app.utils.cuid import generate_cuid
from app.errors import bad_request, not_found

class GuessService:
    @staticmethod
    async def get_round_words(
        db: AsyncSession,
        participant_id: str,
        room_id: str
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

        stmt_chits = select(ChitMessage).where(ChitMessage.roundId == current_round.id)
        res_chits = await db.execute(stmt_chits)
        chits = list(res_chits.scalars().all())

        return [
            RoundWordDTO(
                chitId=c.id,
                body=c.body,
                isOwnWord=(c.senderId == participant_id)
            )
            for c in chits
        ]

    @staticmethod
    async def submit_guesses(
        db: AsyncSession,
        participant_id: str,
        room_id: str,
        guesses: List[ChitGuessItem]
    ) -> bool:
        stmt_round = (
            select(GameRound)
            .where(GameRound.roomId == room_id)
            .order_by(GameRound.roundNumber.desc())
        )
        res_round = await db.execute(stmt_round)
        current_round = res_round.scalars().first()

        if not current_round or current_round.status != RoundStatus.guessing:
            raise bad_request("Guessing is not open for this round.")

        # Clear any prior guesses for this participant in this round
        stmt_del = delete(RoundGuess).where(
            RoundGuess.roundId == current_round.id,
            RoundGuess.guesserId == participant_id
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
            )
            db.add(guess_record)

        await db.flush()
        return True

    @staticmethod
    async def check_all_guesses_submitted(db: AsyncSession, room_id: str) -> bool:
        """Check if all connected, active participants have submitted guesses for current round."""
        stmt_round = (
            select(GameRound)
            .where(GameRound.roomId == room_id)
            .order_by(GameRound.roundNumber.desc())
        )
        res_round = await db.execute(stmt_round)
        current_round = res_round.scalars().first()

        if not current_round or current_round.status != RoundStatus.guessing:
            return False

        # Active participants count
        stmt_active = select(func.count()).select_from(Participant).where(
            Participant.roomId == room_id,
            Participant.removed == False,
            Participant.connected == True
        )
        res_active = await db.execute(stmt_active)
        total_active = res_active.scalar() or 0

        if total_active <= 1:
            return True

        # Count unique guessers for current round
        stmt_guessers = select(func.count(func.distinct(RoundGuess.guesserId))).where(
            RoundGuess.roundId == current_round.id
        )
        res_guessers = await db.execute(stmt_guessers)
        guessers_count = res_guessers.scalar() or 0

        return guessers_count >= total_active

    @staticmethod
    async def calculate_and_reveal_scores(db: AsyncSession, room_id: str) -> RoundResultsDTO:
        stmt_round = (
            select(GameRound)
            .where(GameRound.roomId == room_id)
            .order_by(GameRound.roundNumber.desc())
        )
        res_round = await db.execute(stmt_round)
        current_round = res_round.scalars().first()

        if not current_round:
            raise not_found("No active round found to calculate scores.")

        stmt_room = select(Room).where(Room.id == room_id)
        res_room = await db.execute(stmt_room)
        room = res_room.scalars().first()

        # Fetch all participants for name and score mapping
        stmt_p = select(Participant).where(Participant.roomId == room_id)
        res_p = await db.execute(stmt_p)
        participants = list(res_p.scalars().all())
        participant_map = {p.id: p for p in participants}

        # Fetch all chits for this round
        stmt_chits = select(ChitMessage).where(ChitMessage.roundId == current_round.id)
        res_chits = await db.execute(stmt_chits)
        chits = list(res_chits.scalars().all())
        chit_author_map = {c.id: c.senderId for c in chits}

        # Fetch all guesses for this round
        stmt_guesses = select(RoundGuess).where(RoundGuess.roundId == current_round.id)
        res_guesses = await db.execute(stmt_guesses)
        guesses = list(res_guesses.scalars().all())

        # If not already revealed, calculate +100 pts per correct guess
        if not current_round.identitiesRevealed:
            for g in guesses:
                real_author_id = chit_author_map.get(g.chitId)
                if real_author_id and g.guessedSenderId == real_author_id:
                    g.isCorrect = True
                    guesser = participant_map.get(g.guesserId)
                    if guesser:
                        guesser.score += 100
                        db.add(guesser)
                db.add(g)

            current_round.identitiesRevealed = True
            current_round.status = RoundStatus.revealed
            db.add(current_round)

            if room:
                room.status = RoomStatus.revealed
                db.add(room)

            await db.flush()

        # Build reveal details per chit
        chits_detail: List[RoundRevealDetailDTO] = []
        for c in chits:
            author = participant_map.get(c.senderId)
            author_name = author.displayName if author else "Unknown"

            correct_guesser_names = []
            guesses_summary = []

            for g in guesses:
                if g.chitId == c.id:
                    guesser = participant_map.get(g.guesserId)
                    guessed_player = participant_map.get(g.guessedSenderId)
                    guesser_name = guesser.displayName if guesser else "Player"
                    guessed_name = guessed_player.displayName if guessed_player else "Player"

                    is_corr = (g.guessedSenderId == c.senderId)
                    if is_corr:
                        correct_guesser_names.append(guesser_name)

                    guesses_summary.append(
                        GuessSummaryItem(
                            guesserName=guesser_name,
                            guessedPlayerName=guessed_name,
                            isCorrect=is_corr
                        )
                    )

            chits_detail.append(
                RoundRevealDetailDTO(
                    chitId=c.id,
                    body=c.body,
                    authorParticipantId=c.senderId,
                    authorDisplayName=author_name,
                    correctGuessers=correct_guesser_names,
                    guessesSummary=guesses_summary
                )
            )

        leaderboard = await GuessService.get_leaderboard(db, room_id)
        is_final = bool(room and current_round.roundNumber >= room.totalRounds)

        return RoundResultsDTO(
            roundNumber=current_round.roundNumber,
            totalRounds=room.totalRounds if room else 3,
            isFinalRound=is_final,
            chits=chits_detail,
            leaderboard=leaderboard
        )

    @staticmethod
    async def get_leaderboard(db: AsyncSession, room_id: str) -> List[LeaderboardItemDTO]:
        stmt = (
            select(Participant)
            .where(
                Participant.roomId == room_id,
                Participant.removed == False
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
                    role=p.role.value
                )
            )
        return leaderboard
