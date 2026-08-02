import { participantRepository } from '../repositories/participant.repository.js';
import { aliasRepository } from '../repositories/alias.repository.js';
import { roundRepository } from '../repositories/round.repository.js';
import { ParticipantRole } from '../types/enums.js';
import crypto from 'crypto';
import { prisma } from '../config/prisma.js';

export const aliasService = {
  async generateAliases(roundId: string, aliasEpoch: number): Promise<void> {
    const round = await roundRepository.findById(roundId);
    if (!round) return;

    const participants = await participantRepository.findByRoomId(round.roomId);
    const players = participants.filter(p => p.role === ParticipantRole.player);

    // Shuffle using crypto
    const shuffled = [...players];
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = crypto.randomInt(i + 1);
      [shuffled[i], shuffled[j]] = [shuffled[j]!, shuffled[i]!];
    }

    const aliasData = shuffled.map((p, index) => {
      // Generate a new random opaque ID
      const opaqueAliasId = crypto.randomBytes(16).toString('hex');
      return {
        roundId,
        aliasEpoch,
        participantId: p.id,
        aliasNumber: index + 1,
        opaqueAliasId,
      };
    });

    await prisma.$transaction(async (tx) => {
      await tx.roundAlias.deleteMany({ where: { roundId, aliasEpoch } });
      await tx.roundAlias.createMany({ data: aliasData });
    });
  },

  async reshuffleAliases(roundId: string): Promise<void> {
    const round = await roundRepository.findById(roundId);
    if (!round) return;

    const newEpoch = round.aliasEpoch + 1;
    await this.generateAliases(roundId, newEpoch);
    await roundRepository.updateAliasEpoch(roundId, newEpoch);
  },

  async resolveAliasToParticipant(opaqueAliasId: string): Promise<string | null> {
    const alias = await aliasRepository.findByOpaqueId(opaqueAliasId);
    return alias ? alias.participantId : null;
  },

  async getAliasMapping(roundId: string, aliasEpoch: number) {
    const aliases = await aliasRepository.findByRoundAndEpoch(roundId, aliasEpoch);
    return aliases.reduce((acc, a) => {
      acc[a.participantId] = a;
      return acc;
    }, {} as Record<string, typeof aliases[0]>);
  }
};
