import { participantRepository } from '../repositories/participant.repository.js';
import { chitRepository } from '../repositories/chit.repository.js';
import { roundRepository } from '../repositories/round.repository.js';
import { ParticipantRole } from '../types/enums.js';
import { AppError } from '../errors/app-error.js';
import { ERROR_CODES } from '../errors/error-codes.js';
import { sessionService } from './session.service.js';
import { io } from '../server.js';
import { emitPlayerRemoved, emitRoomStateUpdated, emitPlayerActivityUpdated } from '../sockets/emitters/room.emitter.js';

export const participantService = {
  async getPlayerActivity(roomId: string, currentParticipantId: string, role: ParticipantRole): Promise<any[]> {
    const participants = await participantRepository.findByRoomId(roomId);
    const round = await roundRepository.findCurrentByRoomId(roomId);
    
    let chitsMap: Record<string, boolean> = {};
    if (round) {
      const chits = await chitRepository.findByRoundId(round.id);
      chits.forEach(chit => {
        chitsMap[chit.senderId] = true;
      });
    }

    return participants
      .filter(p => p.role !== ParticipantRole.owner)
      .map(p => ({
        displayName: p.displayName,
        alias: p.displayName,
        aliasId: p.id,
        isCurrentPlayer: p.id === currentParticipantId,
        hasSubmitted: !!chitsMap[p.id],
        connected: p.connected,
      }));
  },

  async getManageablePlayers(roomId: string): Promise<any[]> {
    const activity = await this.getPlayerActivity(roomId, '', ParticipantRole.owner);
    return activity;
  },

  async removePlayer(roomId: string, participantId: string): Promise<void> {
    const participant = await participantRepository.findById(participantId);
    if (!participant || participant.roomId !== roomId) {
      throw AppError.notFound(ERROR_CODES.PLAYER_NOT_FOUND, 'Player not found');
    }

    if (participant.role === ParticipantRole.owner) {
      throw AppError.forbidden(ERROR_CODES.NOT_ROOM_OWNER, 'Cannot remove the room owner');
    }

    await participantRepository.updateRemoved(participantId, true);
    await sessionService.invalidateSession(participantId);

    emitPlayerRemoved(io, participantId);
    
    // Also trigger activity and room state updates
    emitRoomStateUpdated(io, roomId);
    emitPlayerActivityUpdated(io, roomId);
  },

  async reconnectParticipant(participantId: string): Promise<void> {
    await participantRepository.updateConnected(participantId, true);
  }
};
