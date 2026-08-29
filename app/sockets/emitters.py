from typing import Dict, Any, Optional
from app.sockets.server import sio

async def emit_room_state_updated(room_id: str, data: Optional[Dict[str, Any]] = None) -> None:
    """Broadcast state update event to all room participants."""
    await sio.emit("room:state-updated", data or {}, room=f"room:{room_id}")

async def emit_player_activity_updated(room_id: str) -> None:
    """Broadcast activity update event so all clients re-fetch their player list."""
    await sio.emit("room:player-activity-updated", {}, room=f"room:{room_id}")

async def emit_player_joined(room_id: str, display_name: str, player_count: int) -> None:
    """Emit player joined notifications."""
    await sio.emit("room:player-joined", {"displayName": display_name, "playerCount": player_count}, room=f"room:{room_id}")
    await emit_player_activity_updated(room_id)

async def emit_player_left(room_id: str, display_name: str, player_count: int) -> None:
    """Emit player left notifications."""
    await sio.emit("room:player-left", {"displayName": display_name, "playerCount": player_count}, room=f"room:{room_id}")
    await emit_player_activity_updated(room_id)

async def emit_player_removed(participant_id: str) -> None:
    """Notify a specific participant that they were removed by the host."""
    await sio.emit("player:removed", {}, room=f"participant:{participant_id}")

async def emit_room_ended(room_id: str) -> None:
    """Notify all participants that the room was ended."""
    await sio.emit("room:ended", {}, room=f"room:{room_id}")

async def emit_submission_count(room_id: str, submitted: int, total: int) -> None:
    """Send submission counter to the host."""
    await sio.emit("host:submission-count", {"submitted": submitted, "total": total}, room=f"role:{room_id}:owner")

async def emit_submission_status(participant_id: str, status: Dict[str, Any]) -> None:
    """Send submission status to specific player."""
    await sio.emit("player:submission-status", status, room=f"participant:{participant_id}")
