import jwt from 'jsonwebtoken';
import { env } from '../config/env.js';
import { ParticipantRole } from '../types/enums.js';

export interface ParticipantSession {
  participantId: string;
  roomId: string;
  role: ParticipantRole;
  sessionVersion: number;
}

export function signToken(payload: ParticipantSession): string {
  return jwt.sign(payload, env.JWT_SECRET, { expiresIn: '24h' });
}

export function verifyToken(token: string): ParticipantSession {
  return jwt.verify(token, env.JWT_SECRET) as ParticipantSession;
}
