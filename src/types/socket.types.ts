import { HostRoomViewDTO, PlayerRoomViewDTO } from '../dto/room.dto.js';
import { ParticipantRole } from './enums.js';
import { PlayerActivityItemDTO, HostActivityItemDTO } from '../dto/participant.dto.js';
import { AnonymousInboxDTO } from '../dto/inbox.dto.js';
import { SubmissionStatusDTO } from '../dto/submission.dto.js';
import { RevealResultsDTO } from '../dto/reveal.dto.js';

export interface ServerToClientEvents {
  'room:state-updated': (state: HostRoomViewDTO | PlayerRoomViewDTO) => void;
  'room:player-joined': (data: { displayName?: string, alias?: string, playerCount: number }) => void;
  'room:player-left': (data: { displayName?: string, alias?: string, playerCount: number }) => void;
  'room:player-activity-updated': (data: PlayerActivityItemDTO[] | HostActivityItemDTO[]) => void;
  'host:submission-count': (data: { submitted: number, total: number }) => void;
  'host:anonymous-inbox-updated': (data: AnonymousInboxDTO) => void;
  'player:submission-status': (data: SubmissionStatusDTO) => void;
  'room:identities-revealed': (data: RevealResultsDTO) => void;
  'player:removed': (data: { participantId: string }) => void;
  'room:ended': (data: { roomId: string }) => void;
  'room:round-started': (data: { roomId: string, roundNumber: number }) => void;
}

export interface ClientToServerEvents {
  'submission:submit': (data: { body: string }, callback: (res: any) => void) => void;
  'submission:edit': (data: { body: string }, callback: (res: any) => void) => void;
  'submission:delete': (callback: (res: any) => void) => void;
}

export interface InterServerEvents {
  ping: () => void;
}

export interface SocketData {
  participantId: string;
  roomId: string;
  role: ParticipantRole;
  sessionVersion: number;
}
