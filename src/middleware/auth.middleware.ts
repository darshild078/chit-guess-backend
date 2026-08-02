import { Request, Response, NextFunction } from 'express';
import { verifyToken } from '../utils/jwt.js';
import { AppError } from '../errors/app-error.js';
import { ERROR_CODES } from '../errors/error-codes.js';
import { participantRepository } from '../repositories/participant.repository.js';
import jwt from 'jsonwebtoken';

export async function authMiddleware(req: Request, res: Response, next: NextFunction) {
  try {
    let token = req.headers.authorization?.split(' ')[1];

    if (!token && req.headers.cookie) {
      const match = req.headers.cookie.match(/(?:^|;)\s*auth_token=([^;]+)/);
      if (match) token = match[1];
    }

    if (!token) {
      throw AppError.unauthorized(ERROR_CODES.INVALID_SESSION, 'Please join or create a room to continue.');
    }

    const payload = verifyToken(token);
    
    const participant = await participantRepository.findById(payload.participantId);
    if (!participant) {
      throw AppError.unauthorized(ERROR_CODES.PLAYER_NOT_FOUND, 'Your session was not found. Please rejoin the room.');
    }
    if (participant.removed) {
      throw AppError.forbidden(ERROR_CODES.PLAYER_REMOVED, 'You have been removed from this room by the host.');
    }
    if (participant.sessionVersion !== payload.sessionVersion) {
      throw AppError.unauthorized(ERROR_CODES.SESSION_EXPIRED, 'Your session has expired. Please rejoin the room.');
    }

    req.participant = {
      participantId: participant.id,
      roomId: participant.roomId,
      role: participant.role,
      sessionVersion: participant.sessionVersion,
    };

    next();
  } catch (error) {
    if (error instanceof jwt.TokenExpiredError) {
      next(AppError.unauthorized(ERROR_CODES.SESSION_EXPIRED, 'Your session token has expired. Please rejoin.'));
    } else if (error instanceof jwt.JsonWebTokenError) {
      next(AppError.unauthorized(ERROR_CODES.INVALID_SESSION, 'Invalid session token. Please rejoin.'));
    } else {
      next(error);
    }
  }
}
