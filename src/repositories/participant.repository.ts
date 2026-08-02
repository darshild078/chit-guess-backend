import { prisma } from '../config/prisma.js';
import { ParticipantRole } from '../types/enums.js';

export const participantRepository = {
  create(data: { roomId: string; displayName: string; role: ParticipantRole; connected?: boolean }) {
    return prisma.participant.create({
      data,
    });
  },

  findById(id: string) {
    return prisma.participant.findUnique({
      where: { id },
    });
  },

  findByRoomId(roomId: string) {
    return prisma.participant.findMany({
      where: { roomId, removed: false },
      orderBy: { joinedAt: 'asc' },
    });
  },

  findByRoomIdAndName(roomId: string, displayName: string) {
    return prisma.participant.findUnique({
      where: { roomId_displayName: { roomId, displayName } },
    });
  },

  updateConnected(id: string, connected: boolean) {
    return prisma.participant.update({
      where: { id },
      data: { connected, lastSeenAt: new Date() },
    });
  },

  updateRemoved(id: string, removed: boolean) {
    return prisma.participant.update({
      where: { id },
      data: { removed },
    });
  },

  incrementSessionVersion(id: string) {
    return prisma.participant.update({
      where: { id },
      data: { sessionVersion: { increment: 1 } },
    });
  },

  countActiveByRoom(roomId: string) {
    return prisma.participant.count({
      where: { roomId, removed: false, connected: true },
    });
  },
};
