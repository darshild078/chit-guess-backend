import { participantRepository } from '../repositories/participant.repository.js';
import { signToken, ParticipantSession } from '../utils/jwt.js';

export const sessionService = {
  createSession(payload: ParticipantSession): string {
    return signToken(payload);
  },

  async invalidateSession(participantId: string): Promise<void> {
    await participantRepository.incrementSessionVersion(participantId);
  }
};
