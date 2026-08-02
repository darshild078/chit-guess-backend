import { prisma } from '../config/prisma.js';

export const chitRepository = {
  create(data: { roomId: string; roundId: string; senderId: string; body: string }) {
    return prisma.chitMessage.create({
      data,
    });
  },

  findByRoundAndSender(roundId: string, senderId: string) {
    return prisma.chitMessage.findUnique({
      where: { roundId_senderId: { roundId, senderId } },
    });
  },

  findByRoundId(roundId: string) {
    return prisma.chitMessage.findMany({
      where: { roundId },
    });
  },

  update(id: string, data: { body: string }) {
    return prisma.chitMessage.update({
      where: { id },
      data,
    });
  },

  delete(id: string) {
    return prisma.chitMessage.delete({
      where: { id },
    });
  },

  markRead(id: string, isRead: boolean) {
    return prisma.chitMessage.update({
      where: { id },
      data: { isRead },
    });
  },

  markGuessed(id: string, isGuessed: boolean, guessedParticipantId?: string) {
    return prisma.chitMessage.update({
      where: { id },
      data: { isGuessed, guessedParticipantId },
    });
  },

  countByRound(roundId: string) {
    return prisma.chitMessage.count({
      where: { roundId },
    });
  },
};
