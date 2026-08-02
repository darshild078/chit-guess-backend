import { prisma } from '../config/prisma.js';

export const aliasRepository = {
  createMany(data: { roundId: string; aliasEpoch: number; participantId: string; aliasNumber: number; opaqueAliasId: string }[]) {
    return prisma.roundAlias.createMany({
      data,
    });
  },

  findByRoundAndEpoch(roundId: string, aliasEpoch: number) {
    return prisma.roundAlias.findMany({
      where: { roundId, aliasEpoch },
    });
  },

  findByOpaqueId(opaqueAliasId: string) {
    return prisma.roundAlias.findUnique({
      where: { opaqueAliasId },
    });
  },

  deleteByRoundAndEpoch(roundId: string, aliasEpoch: number) {
    return prisma.roundAlias.deleteMany({
      where: { roundId, aliasEpoch },
    });
  },
};
