import { Request, Response, NextFunction } from 'express';
import { AppError } from '../errors/app-error.js';
import { ERROR_CODES } from '../errors/error-codes.js';

export function roomMemberMiddleware(req: Request, res: Response, next: NextFunction) {
  if (!req.participant) {
    return next(AppError.unauthorized(ERROR_CODES.INVALID_SESSION, 'Not authenticated'));
  }

  const { roomId } = req.params;
  if (!roomId || req.participant.roomId !== roomId) {
    return next(AppError.forbidden(ERROR_CODES.NOT_ROOM_MEMBER, 'Not a member of this room'));
  }

  next();
}
