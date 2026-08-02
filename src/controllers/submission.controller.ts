import { Request, Response, NextFunction } from 'express';
import { submissionService } from '../services/submission.service.js';
import { io } from '../server.js';
import { emitPlayerActivityUpdated } from '../sockets/emitters/room.emitter.js';

export const submissionController = {
  async getSubmission(req: Request, res: Response, next: NextFunction) {
    try {
      const { participantId, roomId } = req.participant!;
      const result = await submissionService.getMySubmission(participantId, roomId);
      res.json({ success: true, data: result });
    } catch (error) { next(error); }
  },

  async submitChit(req: Request, res: Response, next: NextFunction) {
    try {
      const { participantId, roomId } = req.participant!;
      const { body } = req.body;
      await submissionService.submitChit(participantId, roomId, body);
      await emitPlayerActivityUpdated(io, roomId);
      res.status(201).json({ success: true, data: null });
    } catch (error) { next(error); }
  },

  async editChit(req: Request, res: Response, next: NextFunction) {
    try {
      const { participantId, roomId } = req.participant!;
      const { body } = req.body;
      await submissionService.editChit(participantId, roomId, body);
      res.json({ success: true, data: null });
    } catch (error) { next(error); }
  },

  async deleteChit(req: Request, res: Response, next: NextFunction) {
    try {
      const { participantId, roomId } = req.participant!;
      await submissionService.deleteChit(participantId, roomId);
      await emitPlayerActivityUpdated(io, roomId);
      res.json({ success: true, data: null });
    } catch (error) { next(error); }
  },
};
