import json
import random
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.room import Room
from app.models.round import GameRound
from app.models.participant import Participant
from app.models.chit import ChitMessage
from app.models.guess import RoundGuess
from app.models.enums import RoomStatus, RoundStatus
from app.schemas.submission import RoundPromptInfoDTO
from app.data.prompt_packs import (
    get_random_confession_prompt,
    get_random_chameleon_round,
    get_random_roast_prompt,
)
from app.utils.cuid import generate_cuid
from app.services.alias_service import AliasService
from app.errors import not_found, bad_request

class RoundService:
    @staticmethod
    async def get_current_round(db: AsyncSession, room_id: str) -> Optional[GameRound]:
        stmt = (
            select(GameRound)
            .where(GameRound.roomId == room_id)
            .order_by(GameRound.roundNumber.desc())
        )
        res = await db.execute(stmt)
        return res.scalars().first()

    @staticmethod
    async def start_round(db: AsyncSession, room_id: str) -> GameRound:
        stmt = select(Room).where(Room.id == room_id)
        res = await db.execute(stmt)
        room = res.scalars().first()
        if not room:
            raise not_found("Room not found.")

        new_round_number = room.currentRoundNumber + 1
        room.currentRoundNumber = new_round_number
        room.status = RoomStatus.submissions_open
        db.add(room)

        # Fetch active participants
        stmt_p = select(Participant).where(
            Participant.roomId == room_id,
            Participant.removed == False,
            Participant.connected == True,
        )
        res_p = await db.execute(stmt_p)
        active_participants = list(res_p.scalars().all())
        active_names = [p.displayName for p in active_participants]

        # Mode-specific round parameters
        prompt = None
        secret_topic = None
        secret_word = None
        chameleon_id = None
        word_choices_json = None

        game_mode = room.gameMode or "confessions"

        if game_mode == "confessions":
            prompt = get_random_confession_prompt(room.promptCategory, room.customPrompt)
        elif game_mode == "chameleon":
            cham_data = get_random_chameleon_round()
            secret_topic = cham_data["topic"]
            secret_word = cham_data["secretWord"]
            word_choices_json = json.dumps(cham_data["wordChoices"])
            if active_participants:
                chosen_cham = random.choice(active_participants)
                chameleon_id = chosen_cham.id
        elif game_mode == "roasts":
            prompt = get_random_roast_prompt(active_names, room.customPrompt)

        now = datetime.now(timezone.utc)
        new_round = GameRound(
            id=generate_cuid(),
            roomId=room_id,
            roundNumber=new_round_number,
            status=RoundStatus.submissions_open,
            aliasEpoch=0,
            identitiesRevealed=False,
            prompt=prompt,
            secretTopic=secret_topic,
            secretWord=secret_word,
            chameleonParticipantId=chameleon_id,
            wordChoices=word_choices_json,
            chameleonEscaped=False,
            chameleonGuessedWord=False,
            submissionsOpenedAt=now,
            createdAt=now,
        )
        db.add(new_round)
        await db.flush()

        await AliasService.generate_aliases(db, new_round)
        return new_round

    @staticmethod
    async def get_round_prompt_info(
        db: AsyncSession, room_id: str, participant_id: str
    ) -> RoundPromptInfoDTO:
        round_obj = await RoundService.get_current_round(db, room_id)
        if not round_obj:
            raise not_found("No active round found.")

        stmt_room = select(Room).where(Room.id == room_id)
        res_room = await db.execute(stmt_room)
        room = res_room.scalars().first()

        game_mode = room.gameMode if room else "confessions"
        is_cham = bool(round_obj.chameleonParticipantId == participant_id)

        choices = []
        if round_obj.wordChoices:
            try:
                choices = json.loads(round_obj.wordChoices)
            except Exception:
                choices = []

        # PRIVACY RULE: If participant is Chameleon, secretWord is hidden (None)
        safe_secret_word = None if is_cham else round_obj.secretWord

        return RoundPromptInfoDTO(
            roundNumber=round_obj.roundNumber,
            totalRounds=room.totalRounds if room else 3,
            gameMode=game_mode,
            prompt=round_obj.prompt,
            secretTopic=round_obj.secretTopic,
            secretWord=safe_secret_word,
            isChameleon=is_cham,
            wordChoices=choices if is_cham else [],
        )

    @staticmethod
    async def advance_to_guessing(db: AsyncSession, room_id: str) -> GameRound:
        round_obj = await RoundService.get_current_round(db, room_id)
        if not round_obj:
            raise not_found("No active round found to advance to guessing.")

        now = datetime.now(timezone.utc)
        round_obj.status = RoundStatus.guessing
        round_obj.submissionsClosedAt = now
        db.add(round_obj)

        stmt = select(Room).where(Room.id == room_id)
        res = await db.execute(stmt)
        room = res.scalars().first()
        if room:
            room.status = RoomStatus.guessing
            db.add(room)

        await db.flush()
        return round_obj

    @staticmethod
    async def advance_to_reveal(db: AsyncSession, room_id: str) -> GameRound:
        round_obj = await RoundService.get_current_round(db, room_id)
        if not round_obj:
            raise not_found("No active round found to reveal.")

        now = datetime.now(timezone.utc)
        round_obj.status = RoundStatus.revealed
        round_obj.identitiesRevealed = True
        round_obj.revealedAt = now
        db.add(round_obj)

        stmt = select(Room).where(Room.id == room_id)
        res = await db.execute(stmt)
        room = res.scalars().first()
        if room:
            if room.currentRoundNumber >= room.totalRounds:
                room.status = RoomStatus.completed
            else:
                room.status = RoomStatus.revealed
            db.add(room)

        await db.flush()
        return round_obj

    @staticmethod
    async def check_all_submissions_done(db: AsyncSession, room_id: str) -> bool:
        round_obj = await RoundService.get_current_round(db, room_id)
        if not round_obj or round_obj.status != RoundStatus.submissions_open:
            return False

        stmt_active = select(func.count()).select_from(Participant).where(
            Participant.roomId == room_id,
            Participant.removed == False,
            Participant.connected == True
        )
        res_active = await db.execute(stmt_active)
        total_active = res_active.scalar() or 0

        if total_active <= 0:
            return False

        stmt_chits = select(func.count()).select_from(ChitMessage).where(
            ChitMessage.roundId == round_obj.id
        )
        res_chits = await db.execute(stmt_chits)
        submitted_count = res_chits.scalar() or 0

        return submitted_count >= total_active
