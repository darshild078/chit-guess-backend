from typing import List, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.participant import Participant
from app.models.round import GameRound
from app.models.chit import ChitMessage
from app.models.guess import RoundGuess
from app.models.enums import ParticipantRole, RoundStatus
from app.schemas.participant import (
    PlayerActivityItemDTO,
    HostActivityItemDTO,
    HostManagePlayerDTO,
)
from app.services.alias_service import AliasService
from app.errors import not_found, bad_request

class ParticipantService:
    @staticmethod
    async def get_player_activity(
        db: AsyncSession,
        room_id: str,
        current_participant: Participant
    ) -> List[PlayerActivityItemDTO]:
        stmt_round = (
            select(GameRound)
            .where(GameRound.roomId == room_id)
            .order_by(GameRound.roundNumber.desc())
        )
        res_round = await db.execute(stmt_round)
        current_round = res_round.scalars().first()

        submitted_sender_ids = set()
        guessed_sender_ids = set()

        if current_round:
            stmt_chits = select(ChitMessage.senderId).where(ChitMessage.roundId == current_round.id)
            res_chits = await db.execute(stmt_chits)
            submitted_sender_ids = set(res_chits.scalars().all())

            stmt_guesses = select(RoundGuess.guesserId).where(RoundGuess.roundId == current_round.id)
            res_guesses = await db.execute(stmt_guesses)
            guessed_sender_ids = set(res_guesses.scalars().all())

        stmt_players = (
            select(Participant)
            .where(
                Participant.roomId == room_id,
                Participant.removed == False
            )
            .order_by(Participant.score.desc(), Participant.joinedAt.asc())
        )
        res_players = await db.execute(stmt_players)
        players = list(res_players.scalars().all())

        items = []
        for player in players:
            items.append(
                PlayerActivityItemDTO(
                    participantId=player.id,
                    displayName=player.displayName,
                    isCurrentPlayer=(player.id == current_participant.id),
                    hasSubmitted=(player.id in submitted_sender_ids),
                    hasGuessed=(player.id in guessed_sender_ids),
                    connected=player.connected,
                    score=player.score,
                    role=player.role.value
                )
            )
        return items

    @staticmethod
    async def get_manageable_players(db: AsyncSession, room_id: str) -> List[HostManagePlayerDTO]:
        stmt_players = (
            select(Participant)
            .where(
                Participant.roomId == room_id,
                Participant.removed == False
            )
            .order_by(Participant.joinedAt.asc())
        )
        res_players = await db.execute(stmt_players)
        players = list(res_players.scalars().all())

        return [
            HostManagePlayerDTO(
                aliasId=p.id,
                alias=p.displayName,
                connected=p.connected,
                hasSubmitted=False
            )
            for p in players
        ]

    @staticmethod
    async def remove_player_by_id(
        db: AsyncSession,
        room_id: str,
        target_participant_id: str
    ) -> str:
        stmt_p = select(Participant).where(
            Participant.id == target_participant_id,
            Participant.roomId == room_id
        )
        res_p = await db.execute(stmt_p)
        participant = res_p.scalars().first()

        if not participant:
            raise not_found("Player not found in this room.")

        if participant.role == ParticipantRole.owner:
            raise bad_request("The host cannot be removed from the room.")

        participant.removed = True
        participant.connected = False
        participant.sessionVersion += 1
        db.add(participant)
        await db.flush()

        return participant.id
