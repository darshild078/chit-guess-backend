import { Socket, Server } from 'socket.io';
import { participantService } from '../../services/participant.service.js';
import { emitPlayerJoined, emitPlayerLeft, emitPlayerActivityUpdated, emitRoomStateUpdated } from '../emitters/room.emitter.js';
import { participantRepository } from '../../repositories/participant.repository.js';
import { ParticipantRole } from '../../types/enums.js';
import { ServerToClientEvents, ClientToServerEvents, InterServerEvents, SocketData } from '../../types/socket.types.js';

type IOSocket = Socket<ClientToServerEvents, ServerToClientEvents, InterServerEvents, SocketData>;
type IOServer = Server<ClientToServerEvents, ServerToClientEvents, InterServerEvents, SocketData>;

export async function handleRoomConnection(io: IOServer, socket: IOSocket) {
  const { participantId, roomId, role } = socket.data;

  // Join socket rooms
  socket.join(`room:${roomId}`);
  socket.join(`participant:${participantId}`);
  socket.join(`role:${roomId}:${role}`);

  // Mark as connected
  await participantService.reconnectParticipant(participantId);
  const participant = await participantRepository.findById(participantId);
  const playerCount = await participantRepository.countActiveByRoom(roomId);

  if (participant && role === ParticipantRole.player) {
    emitPlayerJoined(io, roomId, participant.displayName, participant.displayName, playerCount);
  }

  await emitRoomStateUpdated(io, roomId);
  await emitPlayerActivityUpdated(io, roomId);

  socket.on('disconnect', async () => {
    // Only update connection status to false (do NOT soft-delete/remove player!)
    await participantRepository.updateConnected(participantId, false).catch(() => {});
    
    if (participant && role === ParticipantRole.player) {
      const newPlayerCount = await participantRepository.countActiveByRoom(roomId);
      emitPlayerLeft(io, roomId, participant.displayName, participant.displayName, newPlayerCount);
    }

    await emitRoomStateUpdated(io, roomId);
    await emitPlayerActivityUpdated(io, roomId);
  });
}
