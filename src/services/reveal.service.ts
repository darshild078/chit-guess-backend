import { roundRepository } from '../repositories/round.repository.js';
import { roomRepository } from '../repositories/room.repository.js';
import { chitRepository } from '../repositories/chit.repository.js';
import { participantRepository } from '../repositories/participant.repository.js';
import { AppError } from '../errors/app-error.js';
import { ERROR_CODES } from '../errors/error-codes.js';
import { RoomStatus, RoundStatus } from '../types/enums.js';
import { RevealResultsDTO } from '../dto/reveal.dto.js';
import { prisma } from '../config/prisma.js';

export const revealService = {
  async revealIdentities(roomId: string): Promise<RevealResultsDTO> {
    const round = await roundRepository.findCurrentByRoomId(roomId);
    if (!round) throw AppError.notFound(ERROR_CODES.ROUND_NOT_FOUND, 'No active round');

    if (round.status === RoundStatus.revealed || round.identitiesRevealed) {
      throw AppError.conflict(ERROR_CODES.ALREADY_REVEALED, 'Round already revealed');
    }

    await prisma.$transaction(async (tx) => {
      await tx.gameRound.update({
        where: { id: round.id },
        data: { 
          status: RoundStatus.revealed,
          identitiesRevealed: true,
          revealedAt: new Date(),
        },
      });

      await tx.room.update({
        where: { id: roomId },
        data: { status: RoomStatus.revealed },
      });
    });

    return this.getRevealedResults(roomId);
  },

  async getRevealedResults(roomId: string): Promise<RevealResultsDTO> {
    const round = await roundRepository.findCurrentByRoomId(roomId);
    if (!round) throw AppError.notFound(ERROR_CODES.ROUND_NOT_FOUND, 'No active round');

    if (!round.identitiesRevealed) {
      throw AppError.forbidden(ERROR_CODES.INVALID_ROOM_STATUS, 'Results not yet revealed');
    }

    const chits = await chitRepository.findByRoundId(round.id);
    const participants = await participantRepository.findByRoomId(roomId);
    
    const participantMap = participants.reduce((acc, p) => {
      acc[p.id] = p.displayName;
      return acc;
    }, {} as Record<string, string>);

    const revealedChits = chits.map(chit => ({
      chitId: chit.id,
      senderDisplayName: participantMap[chit.senderId] || 'Unknown Player',
      body: chit.body,
      submittedAt: chit.submittedAt,
      guessedDisplayName: chit.guessedParticipantId ? participantMap[chit.guessedParticipantId] : undefined,
      wasCorrect: chit.guessedParticipantId ? chit.guessedParticipantId === chit.senderId : undefined,
    }));

    return {
      roundNumber: round.roundNumber,
      chits: revealedChits,
    };
  }
};
