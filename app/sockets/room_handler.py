import logging
from sqlalchemy import select
from app.sockets.server import sio
from app.sockets.auth import authenticate_socket
from app.sockets.emitters import emit_player_activity_updated
from app.database import AsyncSessionLocal
from app.models.participant import Participant

logger = logging.getLogger(__name__)

@sio.event
async def connect(sid: str, environ: dict, auth: dict = None):
    session_data = authenticate_socket(environ, auth)
    if not session_data:
        logger.warning(f"Socket connection rejected for sid {sid}: unauthorized")
        return False

    participant_id = session_data["participantId"]
    room_id = session_data["roomId"]
    role = session_data["role"]

    # Save participant data in socket session
    await sio.save_session(sid, {
        "participantId": participant_id,
        "roomId": room_id,
        "role": role,
    })

    # Join rooms
    await sio.enter_room(sid, f"room:{room_id}")
    await sio.enter_room(sid, f"participant:{participant_id}")
    if role == "owner":
        await sio.enter_room(sid, f"role:{room_id}:owner")
    else:
        await sio.enter_room(sid, f"role:{room_id}:players")

    # Mark participant connected in DB
    try:
        async with AsyncSessionLocal() as db:
            stmt = select(Participant).where(Participant.id == participant_id)
            res = await db.execute(stmt)
            participant = res.scalars().first()
            if participant:
                participant.connected = True
                db.add(participant)
                await db.commit()

        await emit_player_activity_updated(room_id)
    except Exception as e:
        logger.error(f"Error marking participant connected: {e}")

    logger.info(f"Socket {sid} connected: participant {participant_id} in room {room_id}")
    return True

@sio.event
async def disconnect(sid: str):
    try:
        session = await sio.get_session(sid)
        if not session:
            return

        participant_id = session.get("participantId")
        room_id = session.get("roomId")

        if participant_id and room_id:
            async with AsyncSessionLocal() as db:
                stmt = select(Participant).where(Participant.id == participant_id)
                res = await db.execute(stmt)
                participant = res.scalars().first()
                if participant:
                    participant.connected = False
                    db.add(participant)
                    await db.commit()

            await emit_player_activity_updated(room_id)
    except Exception as e:
        logger.error(f"Error handling socket disconnect: {e}")
