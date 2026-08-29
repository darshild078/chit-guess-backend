from typing import List, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.participant import Participant
from app.models.round import GameRound
from app.models.chit import ChitMessage
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
    ) -> List[Union[PlayerActivityItemDTO, HostActivityItemDTO]]:
        # Fetch current round for this room
        stmt_round = (
            select(GameRound)
            .where(GameRound.roomId == room_id)
            .order_by(GameRound.roundNumber.desc())
        )
        res_round = await db.execute(stmt_round)
        current_round = res_round.scalars().first()

        # Fetch all submissions for current round if round exists
        submitted_sender_ids = set()
        if current_round:
            stmt_chits = select(ChitMessage.senderId).where(ChitMessage.roundId == current_round.id)
            res_chits = await db.execute(stmt_chits)
            submitted_sender_ids = set(res_chits.scalars().all())

        # Fetch non-owner active participants
        stmt_players = (
            select(Participant)
            .where(
                Participant.roomId == room_id,
                Participant.role == ParticipantRole.player,
                Participant.removed == False
            )
            .order_by(Participant.joinedAt.asc())
        )
        res_players = await db.execute(stmt_players)
        players = list(res_players.scalars().all())

        if current_participant.role == ParticipantRole.owner:
            # HOST VIEW: Return anonymous aliases (Player 1, Player 2) - NO REAL NAMES
            if not current_round:
                return [
                    HostActivityItemDTO(
                        alias=f"Player {idx}",
                        aliasId=player.id,
                        hasSubmitted=False,
                        connected=player.connected
                    )
                    for idx, player in enumerate(players, start=1)
                ]

            aliases = await AliasService.get_or_create_aliases_for_epoch(db, current_round)
            alias_map = {a.participantId: a for a in aliases}

            items = []
            for player in players:
                alias = alias_map.get(player.id)
                if alias:
                    items.append(
                        HostActivityItemDTO(
                            alias=f"Player {alias.aliasNumber}",
                            aliasId=alias.opaqueAliasId,
                            hasSubmitted=player.id in submitted_sender_ids,
                            connected=player.connected
                        )
                    )
            return sorted(items, key=lambda x: int(x.alias.split(" ")[1]) if " " in x.alias else 0)
        else:
            # PLAYER VIEW: Return real display names with submission indicators (NO card content)
            items = []
            for player in players:
                items.append(
                    PlayerActivityItemDTO(
                        displayName=player.displayName,
                        isCurrentPlayer=(player.id == current_participant.id),
                        hasSubmitted=(player.id in submitted_sender_ids),
                        connected=player.connected
                    )
                )
            return items

    @staticmethod
    async def get_manageable_players(db: AsyncSession, room_id: str) -> List[HostManagePlayerDTO]:
        stmt_round = (
            select(GameRound)
            .where(GameRound.roomId == room_id)
            .order_by(GameRound.roundNumber.desc())
        )
        res_round = await db.execute(stmt_round)
        current_round = res_round.scalars().first()

        stmt_players = (
            select(Participant)
            .where(
                Participant.roomId == room_id,
                Participant.role == ParticipantRole.player,
                Participant.removed == False
            )
            .order_by(Participant.joinedAt.asc())
        )
        res_players = await db.execute(stmt_players)
        players = list(res_players.scalars().all())

        if not current_round:
            return [
                HostManagePlayerDTO(
                    aliasId=p.id,
                    alias=f"Player {i}",
                    connected=p.connected,
                    hasSubmitted=False
                )
                for i, p in enumerate(players, start=1)
            ]

        aliases = await AliasService.get_or_create_aliases_for_epoch(db, current_round)
        alias_map = {a.participantId: a for a in aliases}

        items = []
        for p in players:
            alias = alias_map.get(p.id)
            if alias:
                items.append(
                    HostManagePlayerDTO(
                        aliasId=alias.opaqueAliasId,
                        alias=f"Player {alias.aliasNumber}",
                        connected=p.connected,
                        hasSubmitted=False
                    )
                )
        return sorted(items, key=lambda x: int(x.alias.split(" ")[1]) if " " in x.alias else 0)

    @staticmethod
    async def remove_player_by_alias(
        db: AsyncSession,
        room_id: str,
        opaque_alias_id: str
    ) -> str:
        alias = await AliasService.resolve_opaque_alias_id(db, opaque_alias_id)
        if not alias:
            # Fallback if aliasId passed is direct participantId
            stmt_p = select(Participant).where(
                Participant.id == opaque_alias_id,
                Participant.roomId == room_id
            )
            res_p = await db.execute(stmt_p)
            participant = res_p.scalars().first()
        else:
            stmt_p = select(Participant).where(
                Participant.id == alias.participantId,
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
