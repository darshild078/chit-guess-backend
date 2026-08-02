import { Request, Response, NextFunction } from 'express';
import { inboxService } from '../services/inbox.service.js';
import { roundService } from '../services/round.service.js';
import { revealService } from '../services/reveal.service.js';
import { AppError } from '../errors/app-error.js';
import { ERROR_CODES } from '../errors/error-codes.js';

export const inboxController = {
  async getAnonymousInbox(req: Request, res: Response, next: NextFunction) {
    try {
      const { roomId } = req.participant!;
      const round = await roundService.getCurrentRound(roomId);
      if (!round) throw AppError.notFound(ERROR_CODES.ROUND_NOT_FOUND, 'No active round');
      
      const result = await inboxService.getAnonymousInbox(roomId, round.id);
      res.json({ success: true, data: result });
    } catch (error) { next(error); }
  },

  async markRead(req: Request, res: Response, next: NextFunction) {
    try {
      const { roomId } = req.participant!;
      const { anonymousChitId } = req.params;
      const { isRead } = req.body;
      
      await inboxService.markChitRead(anonymousChitId as string, roomId, isRead);
      res.json({ success: true, data: null });
    } catch (error) { next(error); }
  },

  async markGuessed(req: Request, res: Response, next: NextFunction) {
    try {
      const { roomId } = req.participant!;
      const { anonymousChitId } = req.params;
      const { isGuessed, guessedAliasId } = req.body;
      
      await inboxService.markChitGuessed(anonymousChitId as string, roomId, isGuessed, guessedAliasId);
      res.json({ success: true, data: null });
    } catch (error) { next(error); }
  },

  async getResults(req: Request, res: Response, next: NextFunction) {
    try {
      const { roomId } = req.participant!;
      const result = await revealService.getRevealedResults(roomId);
      res.json({ success: true, data: result });
    } catch (error) { next(error); }
  }
};
