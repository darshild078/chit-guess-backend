import { roundRepository } from '../repositories/round.repository.js';
import { chitRepository } from '../repositories/chit.repository.js';
import { aliasService } from './alias.service.js';
import { AppError } from '../errors/app-error.js';
import { ERROR_CODES } from '../errors/error-codes.js';
import { AnonymousInboxDTO } from '../dto/inbox.dto.js';
import { RoundStatus } from '../types/enums.js';

export const inboxService = {
  async getAnonymousInbox(roomId: string, roundId: string): Promise<AnonymousInboxDTO> {
    const round = await roundRepository.findById(roundId);
    if (!round) throw AppError.notFound(ERROR_CODES.ROUND_NOT_FOUND, 'Round not found');

    if (round.status === RoundStatus.waiting) {
      throw AppError.forbidden(ERROR_CODES.SUBMISSIONS_NOT_OPEN, 'Round has not started yet');
    }

    const chits = await chitRepository.findByRoundId(roundId);
    const mappings = await aliasService.getAliasMapping(roundId, round.aliasEpoch);

    const anonymousChits = chits.map(chit => {
      const alias = mappings[chit.senderId];
      if (!alias) return null;

      return {
        anonymousChitId: alias.opaqueAliasId + '-' + chit.id, // Compound ID
        alias: `Player ${alias.aliasNumber}`,
        body: chit.body,
        submittedAt: chit.submittedAt,
        isRead: chit.isRead,
        isGuessed: chit.isGuessed,
      };
    }).filter(c => c !== null);

    return {
      roundNumber: round.roundNumber,
      aliasEpoch: round.aliasEpoch,
      chits: anonymousChits as any,
    };
  },

  async markChitRead(anonymousChitId: string, roomId: string, isRead: boolean): Promise<void> {
    const chitId = anonymousChitId.split('-').slice(1).join('-');
    if (!chitId) throw AppError.badRequest(ERROR_CODES.CHIT_NOT_FOUND, 'Invalid chit ID');

    const chit = await chitRepository.update(chitId, { body: undefined } as any);
    if (!chit) throw AppError.notFound(ERROR_CODES.CHIT_NOT_FOUND, 'Chit not found');

    await chitRepository.markRead(chitId, isRead);
  },

  async markChitGuessed(anonymousChitId: string, roomId: string, isGuessed: boolean, guessedAliasId?: string): Promise<void> {
    const chitId = anonymousChitId.split('-').slice(1).join('-');
    if (!chitId) throw AppError.badRequest(ERROR_CODES.CHIT_NOT_FOUND, 'Invalid chit ID');

    let participantId: string | undefined;
    if (isGuessed && guessedAliasId) {
      const resolved = await aliasService.resolveAliasToParticipant(guessedAliasId);
      if (resolved) participantId = resolved;
    }

    await chitRepository.markGuessed(chitId, isGuessed, participantId);
  }
};
