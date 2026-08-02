import rateLimit from 'express-rate-limit';
import { AppError } from '../errors/app-error.js';
import { ERROR_CODES } from '../errors/error-codes.js';
import { env } from '../config/env.js';

const isDev = env.NODE_ENV === 'development' || env.NODE_ENV === 'test';

const handler = (req: any, res: any, next: any) => {
  next(AppError.tooManyRequests(ERROR_CODES.RATE_LIMITED, 'Too many requests, please try again later'));
};

export const generalLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: isDev ? 10000 : 300,
  handler,
  skip: () => isDev, // Skip rate limiting completely in local development
});

export const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: isDev ? 10000 : 30,
  handler,
  skip: () => isDev,
});

export const joinLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: isDev ? 10000 : 30,
  handler,
  skip: () => isDev,
});

export const submissionLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: isDev ? 10000 : 100,
  handler,
  skip: () => isDev,
});
