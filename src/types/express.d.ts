import { ParticipantRole } from './enums.js';

declare global {
  namespace Express {
    interface Request {
      participant?: {
        participantId: string;
        roomId: string;
        role: ParticipantRole;
        sessionVersion: number;
      };
    }
  }
}
