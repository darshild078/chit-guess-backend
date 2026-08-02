import { prisma } from '../config/prisma.js';
import { RoundStatus } from '../types/enums.js';

export const roundRepository = {
  create(data: { roomId: string; roundNumber: number }) {
    return prisma.gameRound.create({
      data,
    });
  },

  findById(id: string) {
    return prisma.gameRound.findUnique({
      where: { id },
    });
  },

  findCurrentByRoomId(roomId: string) {
    return prisma.gameRound.findFirst({
      where: { roomId },
      orderBy: { roundNumber: 'desc' },
    });
  },

  findByRoomAndNumber(roomId: string, roundNumber: number) {
    return prisma.gameRound.findUnique({
      where: { roomId_roundNumber: { roomId, roundNumber } },
    });
  },

  updateStatus(id: string, status: RoundStatus, extraData: any = {}) {
    return prisma.gameRound.update({
      where: { id },
      data: { status, ...extraData },
    });
  },

  updateAliasEpoch(id: string, aliasEpoch: number) {
    return prisma.gameRound.update({
      where: { id },
      data: { aliasEpoch },
    });
  },

  markRevealed(id: string) {
    return prisma.gameRound.update({
      where: { id },
      data: { 
        status: RoundStatus.revealed, 
        identitiesRevealed: true,
        revealedAt: new Date()
      },
    });
  },
};
