import { Request, Response, NextFunction } from 'express';
import { z } from 'zod';
import { AppError } from '../errors/app-error.js';
import { ERROR_CODES } from '../errors/error-codes.js';

export function validate(schema: z.ZodTypeAny, source: 'body' | 'params' | 'query' = 'body') {
  return (req: Request, res: Response, next: NextFunction) => {
    try {
      const parsed = schema.parse(req[source]);
      req[source] = parsed;
      next();
    } catch (error) {
      if (error instanceof z.ZodError) {
        const fieldErrors: Record<string, string[]> = {};
        error.errors.forEach((err) => {
          if (err.path.length > 0) {
            const key = err.path.join('.');
            if (!fieldErrors[key]) fieldErrors[key] = [];
            fieldErrors[key]!.push(err.message);
          }
        });
        next(new AppError(400, ERROR_CODES.VALIDATION_ERROR, 'Validation failed', fieldErrors));
      } else {
        next(error);
      }
    }
  };
}
