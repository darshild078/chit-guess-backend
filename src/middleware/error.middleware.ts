import { Request, Response, NextFunction } from 'express';
import { AppError } from '../errors/app-error.js';
import { ApiErrorResponse } from '../dto/common.dto.js';
import { ERROR_CODES } from '../errors/error-codes.js';
import { logger } from '../config/logger.js';

export function errorHandler(
  err: Error,
  req: Request,
  res: Response,
  next: NextFunction
) {
  if (err instanceof AppError) {
    const response: ApiErrorResponse = {
      success: false,
      error: {
        code: err.code,
        message: err.message,
        fieldErrors: err.fieldErrors,
      },
    };
    return res.status(err.statusCode).json(response);
  }

  // Log unhandled server errors internally for developers
  logger.error(err, 'Unhandled Server Exception');

  // Return clean, user-friendly JSON error response (never leak stack traces or internal code lines)
  const response: ApiErrorResponse = {
    success: false,
    error: {
      code: ERROR_CODES.INTERNAL_SERVER_ERROR,
      message: 'Something went wrong on our end. Please try again.',
    },
  };

  return res.status(500).json(response);
}
