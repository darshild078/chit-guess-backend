import logging
from app.sockets.server import sio
from app.database import AsyncSessionLocal
from app.services.submission_service import SubmissionService
from app.sockets.emitters import emit_player_activity_updated, emit_submission_status

logger = logging.getLogger(__name__)

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
            submission = await SubmissionService.submit_chit(db, participant_id, room_id, body)
            await db.commit()

        await emit_player_activity_updated(room_id)
        await emit_submission_status(participant_id, {
            "hasSubmitted": True,
            "canEdit": True,
            "canDelete": True,
            "canSubmit": False
        })
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
            submission = await SubmissionService.edit_chit(db, participant_id, room_id, body)
            await db.commit()

        await emit_player_activity_updated(room_id)
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
            await SubmissionService.delete_chit(db, participant_id, room_id)
            await db.commit()

        await emit_player_activity_updated(room_id)
        await emit_submission_status(participant_id, {
            "hasSubmitted": False,
            "canEdit": False,
            "canDelete": False,
            "canSubmit": True
        })
    except Exception as e:
        logger.error(f"Socket delete error: {e}")
