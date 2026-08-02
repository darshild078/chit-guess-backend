import { roundRepository } from '../repositories/round.repository.js';
import { roomRepository } from '../repositories/room.repository.js';
import { aliasService } from './alias.service.js';
import { AppError } from '../errors/app-error.js';
import { ERROR_CODES } from '../errors/error-codes.js';
import { RoomStatus, RoundStatus } from '../types/enums.js';
import { prisma } from '../config/prisma.js';

export const roundService = {
  async startRound(roomId: string) {
    const room = await roomRepository.findById(roomId);
    if (!room) throw AppError.notFound(ERROR_CODES.ROOM_NOT_FOUND, 'Room not found');

    const nextRoundNumber = room.currentRoundNumber + 1;

    const round = await prisma.$transaction(async (tx) => {
      const newRound = await tx.gameRound.create({
        data: {
          roomId,
          roundNumber: nextRoundNumber,
          status: RoundStatus.submissions_open,
          submissionsOpenedAt: new Date(),
        },
      });

      await tx.room.update({
        where: { id: roomId },
        data: { 
          currentRoundNumber: nextRoundNumber,
          status: RoomStatus.submissions_open,
        },
      });

      return newRound;
    });

    await aliasService.generateAliases(round.id, 0);

    return round;
  },

  async openSubmissions(roomId: string) {
    const round = await roundRepository.findCurrentByRoomId(roomId);
    if (!round) throw AppError.notFound(ERROR_CODES.ROUND_NOT_FOUND, 'Round not found');

    await prisma.$transaction(async (tx) => {
      await tx.gameRound.update({
        where: { id: round.id },
        data: { 
          status: RoundStatus.submissions_open,
          submissionsOpenedAt: new Date(),
        },
      });

      await tx.room.update({
        where: { id: roomId },
        data: { status: RoomStatus.submissions_open },
      });
    });
  },

  async closeSubmissions(roomId: string) {
    const round = await roundRepository.findCurrentByRoomId(roomId);
    if (!round) throw AppError.notFound(ERROR_CODES.ROUND_NOT_FOUND, 'Round not found');
    
    if (round.status !== RoundStatus.submissions_open) {
      throw AppError.badRequest(ERROR_CODES.INVALID_ROOM_STATUS, 'Submissions are not open');
    }

    await prisma.$transaction(async (tx) => {
      await tx.gameRound.update({
        where: { id: round.id },
        data: { 
          status: RoundStatus.submissions_closed,
          submissionsClosedAt: new Date(),
        },
      });

      await tx.room.update({
        where: { id: roomId },
        data: { status: RoomStatus.submissions_closed },
      });
    });
  },

  async getCurrentRound(roomId: string) {
    return roundRepository.findCurrentByRoomId(roomId);
  }
};
