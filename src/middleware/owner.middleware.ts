import { Request, Response, NextFunction } from 'express';
import { AppError } from '../errors/app-error.js';
import { ERROR_CODES } from '../errors/error-codes.js';
import { ParticipantRole } from '../types/enums.js';

export function ownerMiddleware(req: Request, res: Response, next: NextFunction) {
  if (!req.participant) {
    return next(AppError.unauthorized(ERROR_CODES.INVALID_SESSION, 'Not authenticated'));
  }

  if (req.participant.role !== ParticipantRole.owner) {
    return next(AppError.forbidden(ERROR_CODES.NOT_ROOM_OWNER, 'Requires room owner privileges'));
  }

  next();
}
