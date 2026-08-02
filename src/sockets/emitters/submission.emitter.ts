import { Server } from 'socket.io';
import { ServerToClientEvents, ClientToServerEvents, InterServerEvents, SocketData } from '../../types/socket.types.js';
import { ParticipantRole } from '../../types/enums.js';
import { SubmissionStatusDTO } from '../../dto/submission.dto.js';

type IOServer = Server<ClientToServerEvents, ServerToClientEvents, InterServerEvents, SocketData>;

export function emitSubmissionCount(io: IOServer, roomId: string, submitted: number, total: number) {
  io.to(`role:${roomId}:${ParticipantRole.owner}`).emit('host:submission-count', { submitted, total });
}

export function emitSubmissionStatusUpdated(io: IOServer, participantId: string, status: SubmissionStatusDTO) {
  io.to(`participant:${participantId}`).emit('player:submission-status', status);
}
