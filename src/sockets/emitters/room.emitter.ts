import { Server } from 'socket.io';
import { ServerToClientEvents, ClientToServerEvents, InterServerEvents, SocketData } from '../../types/socket.types.js';
import { HostRoomViewDTO, PlayerRoomViewDTO } from '../../dto/room.dto.js';
import { ParticipantRole } from '../../types/enums.js';
import { roomService } from '../../services/room.service.js';
import { participantService } from '../../services/participant.service.js';

type IOServer = Server<ClientToServerEvents, ServerToClientEvents, InterServerEvents, SocketData>;

export function emitPlayerJoined(io: IOServer, roomId: string, displayName: string, alias: string, playerCount: number) {
  io.to(`room:${roomId}`).emit('room:player-joined', {
    displayName,
    alias: displayName,
    playerCount,
  });
}

export function emitPlayerLeft(io: IOServer, roomId: string, displayName: string, alias: string, playerCount: number) {
  io.to(`room:${roomId}`).emit('room:player-left', {
    displayName,
    alias: displayName,
    playerCount,
  });
}

export async function emitRoomStateUpdated(io: IOServer, roomId: string) {
  try {
    const hostView = await roomService.getRoomView('', roomId, ParticipantRole.owner);
    io.to(`role:${roomId}:${ParticipantRole.owner}`).emit('room:state-updated', hostView);

    const playerView = await roomService.getRoomView('', roomId, ParticipantRole.player);
    io.to(`role:${roomId}:${ParticipantRole.player}`).emit('room:state-updated', playerView);
  } catch (error) {
    console.error('Failed to emit room state update:', error);
  }
}

export function emitRoomEnded(io: IOServer, roomId: string) {
  io.to(`room:${roomId}`).emit('room:ended', { roomId });
}

export function emitPlayerRemoved(io: IOServer, participantId: string) {
  io.to(`participant:${participantId}`).emit('player:removed', { participantId });
}

export function emitRoundStarted(io: IOServer, roomId: string, roundNumber: number) {
  io.to(`room:${roomId}`).emit('room:round-started', { roomId, roundNumber });
}

export async function emitPlayerActivityUpdated(io: IOServer, roomId: string) {
  try {
    const activity = await participantService.getPlayerActivity(roomId, '', ParticipantRole.owner);
    // Broadcast player activity to the entire room so host and all players update immediately
    io.to(`room:${roomId}`).emit('room:player-activity-updated', activity);
  } catch (error) {
    console.error('Failed to emit player activity update:', error);
  }
}
