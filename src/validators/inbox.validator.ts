import { z } from 'zod';

export const markReadSchema = z.object({
  isRead: z.boolean(),
});

export const markGuessSchema = z.object({
  isGuessed: z.boolean(),
  guessedAliasId: z.string().optional(),
});
