import { z } from 'zod';
import { trimAndClean, isBlankOrEmpty } from '../utils/sanitize.js';

export const createRoomSchema = z.object({
  hostDisplayName: z.string()
    .transform(trimAndClean)
    .refine(val => !isBlankOrEmpty(val), { message: 'Display name cannot be empty' })
    .refine(val => val.length >= 2 && val.length <= 20, { message: 'Display name must be between 2 and 20 characters' }),
  title: z.string().max(50).optional(),
  maxPlayers: z.number().int().min(2).max(30).default(10),
});

export const joinRoomSchema = z.object({
  roomCode: z.string().length(6).regex(/^[ABCDEFGHJKLMNPQRSTUVWXYZ23456789]{6}$/, 'Invalid room code format'),
  displayName: z.string()
    .transform(trimAndClean)
    .refine(val => !isBlankOrEmpty(val), { message: 'Display name cannot be empty' })
    .refine(val => val.length >= 2 && val.length <= 20, { message: 'Display name must be between 2 and 20 characters' }),
});

export const roomCodeParamSchema = z.object({
  roomCode: z.string().length(6),
});
