import { z } from 'zod';
import { trimAndClean, isBlankOrEmpty } from '../utils/sanitize.js';

const chitBodySchema = z.string()
  .transform(trimAndClean)
  .refine(val => !isBlankOrEmpty(val), { message: 'Chit message cannot be empty' })
  .refine(val => val.length >= 1 && val.length <= 200, { message: 'Chit message must be between 1 and 200 characters' });

export const submitChitSchema = z.object({
  body: chitBodySchema,
});

export const editChitSchema = z.object({
  body: chitBodySchema,
});
