import { roundRepository } from '../repositories/round.repository.js';
import { chitRepository } from '../repositories/chit.repository.js';
import { AppError } from '../errors/app-error.js';
import { ERROR_CODES } from '../errors/error-codes.js';
import { RoundStatus } from '../types/enums.js';
import { MySubmissionDTO } from '../dto/submission.dto.js';

export const submissionService = {
  async submitChit(participantId: string, roomId: string, body: string): Promise<void> {
    const round = await roundRepository.findCurrentByRoomId(roomId);
    if (!round) throw AppError.notFound(ERROR_CODES.ROUND_NOT_FOUND, 'No active round');
    if (round.status !== RoundStatus.submissions_open) {
      throw AppError.forbidden(ERROR_CODES.SUBMISSIONS_CLOSED, 'Submissions are closed');
    }

    const existing = await chitRepository.findByRoundAndSender(round.id, participantId);
    if (existing) {
      throw AppError.conflict(ERROR_CODES.ALREADY_SUBMITTED, 'You have already submitted a chit');
    }

    await chitRepository.create({
      roomId,
      roundId: round.id,
      senderId: participantId,
      body,
    });
  },

  async editChit(participantId: string, roomId: string, body: string): Promise<void> {
    const round = await roundRepository.findCurrentByRoomId(roomId);
    if (!round) throw AppError.notFound(ERROR_CODES.ROUND_NOT_FOUND, 'No active round');
    if (round.status !== RoundStatus.submissions_open) {
      throw AppError.forbidden(ERROR_CODES.SUBMISSIONS_CLOSED, 'Submissions are closed');
    }

    const chit = await chitRepository.findByRoundAndSender(round.id, participantId);
    if (!chit) {
      throw AppError.notFound(ERROR_CODES.CHIT_NOT_FOUND, 'Submission not found');
    }

    await chitRepository.update(chit.id, { body });
  },

  async deleteChit(participantId: string, roomId: string): Promise<void> {
    const round = await roundRepository.findCurrentByRoomId(roomId);
    if (!round) throw AppError.notFound(ERROR_CODES.ROUND_NOT_FOUND, 'No active round');
    if (round.status !== RoundStatus.submissions_open) {
      throw AppError.forbidden(ERROR_CODES.SUBMISSIONS_CLOSED, 'Submissions are closed');
    }

    const chit = await chitRepository.findByRoundAndSender(round.id, participantId);
    if (!chit) {
      throw AppError.notFound(ERROR_CODES.CHIT_NOT_FOUND, 'Submission not found');
    }

    await chitRepository.delete(chit.id);
  },

  async getMySubmission(participantId: string, roomId: string): Promise<MySubmissionDTO | null> {
    const round = await roundRepository.findCurrentByRoomId(roomId);
    if (!round) return null;

    const chit = await chitRepository.findByRoundAndSender(round.id, participantId);
    if (!chit) return null;

    return {
      body: chit.body,
      submittedAt: chit.submittedAt,
      updatedAt: chit.updatedAt,
    };
  }
};
