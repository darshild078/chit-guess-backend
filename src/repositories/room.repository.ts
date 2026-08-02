import { prisma } from '../config/prisma.js';
import { RoomStatus } from '../types/enums.js';

export const roomRepository = {
  create(data: { code: string; title?: string; maxPlayers: number; expiresAt: Date; ownerParticipantId?: string }) {
    return prisma.room.create({
      data,
      select: {
        id: true,
        code: true,
        title: true,
        status: true,
        maxPlayers: true,
        locked: true,
        currentRoundNumber: true,
        expiresAt: true,
        ownerParticipantId: true,
      },
    });
  },

  findByCode(code: string) {
    return prisma.room.findUnique({
      where: { code },
      select: {
        id: true,
        code: true,
        title: true,
        status: true,
        maxPlayers: true,
        locked: true,
        currentRoundNumber: true,
        expiresAt: true,
        ownerParticipantId: true,
        _count: {
          select: { participants: { where: { removed: false } } },
        },
      },
    });
  },

  findById(id: string) {
    return prisma.room.findUnique({
      where: { id },
      select: {
        id: true,
        code: true,
        title: true,
        status: true,
        maxPlayers: true,
        locked: true,
        currentRoundNumber: true,
        expiresAt: true,
        ownerParticipantId: true,
      },
    });
  },

  updateStatus(id: string, status: RoomStatus) {
    return prisma.room.update({
      where: { id },
      data: { status },
    });
  },

  updateLocked(id: string, locked: boolean) {
    return prisma.room.update({
      where: { id },
      data: { locked },
    });
  },

  updateCurrentRound(id: string, roundNumber: number) {
    return prisma.room.update({
      where: { id },
      data: { currentRoundNumber: roundNumber },
    });
  },

  delete(id: string) {
    return prisma.room.delete({ where: { id } });
  },
};
