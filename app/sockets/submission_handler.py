import logging
from app.core.database import AsyncSessionLocal
from app.core.logging import logger
from app.services.submission_service import (
    delete_chit,
    edit_chit,
    submit_chit,
)
from app.sockets.emitters import emit_player_activity_updated, emit_submission_status
from app.sockets.server import sio

@sio.on("submission:submit")
async def handle_submit(sid: str, data: dict):
    try:
        session = await sio.get_session(sid)
        if not session:
            return

        participant_id = session.get("participantId")
        room_id = session.get("roomId")
        body = data.get("body", "")

        async with AsyncSessionLocal() as db:
            await submit_chit(db, participant_id, room_id, body)
            await db.commit()
    except Exception as e:
        logger.error(f"Socket submit error: {e}")

@sio.on("submission:edit")
async def handle_edit(sid: str, data: dict):
    try:
        session = await sio.get_session(sid)
        if not session:
            return

        participant_id = session.get("participantId")
        room_id = session.get("roomId")
        body = data.get("body", "")

        async with AsyncSessionLocal() as db:
            await edit_chit(db, participant_id, room_id, body)
            await db.commit()
    except Exception as e:
        logger.error(f"Socket edit error: {e}")

@sio.on("submission:delete")
async def handle_delete(sid: str, data: dict = None):
    try:
        session = await sio.get_session(sid)
        if not session:
            return

        participant_id = session.get("participantId")
        room_id = session.get("roomId")

        async with AsyncSessionLocal() as db:
            await delete_chit(db, participant_id, room_id)
            await db.commit()
    except Exception as e:
        logger.error(f"Socket delete error: {e}")
