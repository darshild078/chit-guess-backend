import logging
from app.core.database import AsyncSessionLocal
from app.core.logging import logger
from app.services.participant_service import set_participant_connection_status
from app.sockets.auth import authenticate_socket
from app.sockets.emitters import emit_player_activity_updated
from app.sockets.server import sio

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

    # Mark participant connected via service
    try:
        async with AsyncSessionLocal() as db:
            await set_participant_connection_status(db, participant_id, connected=True)
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
                await set_participant_connection_status(db, participant_id, connected=False)
                await db.commit()

            await emit_player_activity_updated(room_id)
    except Exception as e:
        logger.error(f"Error handling socket disconnect: {e}")

@sio.on("reaction:send")
async def handle_reaction(sid: str, data: dict):
    try:
        session = await sio.get_session(sid)
        if not session:
            return

        room_id = session.get("roomId")
        participant_id = session.get("participantId")
        emoji = data.get("emoji", "🔥")

        if room_id:
            await sio.emit("reaction:received", {
                "emoji": emoji,
                "senderId": participant_id,
            }, room=f"room:{room_id}")
    except Exception as e:
        logger.error(f"Error broadcasting reaction: {e}")
