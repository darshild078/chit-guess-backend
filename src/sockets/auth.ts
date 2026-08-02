import { Socket } from 'socket.io';
import { verifyToken } from '../utils/jwt.js';
import { participantRepository } from '../repositories/participant.repository.js';
import { ParticipantRole } from '../types/enums.js';

export async function socketAuthMiddleware(socket: Socket, next: (err?: Error) => void) {
  try {
    let token = socket.handshake.auth?.token;
    if (!token && socket.handshake.headers.cookie) {
      const match = socket.handshake.headers.cookie.match(/(?:^|;)\s*auth_token=([^;]+)/);
      if (match) token = match[1];
    }

    if (!token) {
      return next(new Error('Authentication error: No token provided'));
    }

    const payload = verifyToken(token);
    const participant = await participantRepository.findById(payload.participantId);
    
    if (!participant) {
      return next(new Error('Authentication error: Participant not found'));
    }
    if (participant.removed) {
      return next(new Error('Authentication error: Removed from room'));
    }
    if (participant.sessionVersion !== payload.sessionVersion) {
      return next(new Error('Authentication error: Session expired'));
    }

    socket.data = {
      participantId: participant.id,
      roomId: participant.roomId,
      role: participant.role as ParticipantRole,
      sessionVersion: participant.sessionVersion,
    };

    next();
  } catch (error) {
    next(new Error('Authentication error: Invalid session'));
  }
}
