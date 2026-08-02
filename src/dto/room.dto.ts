import { RoomStatus, ParticipantRole } from '../types/enums.js';

export interface RoomCreatedDTO {
  roomId: string;
  roomCode: string;
  participantId: string;
  token: string;
  role: ParticipantRole;
}

export interface RoomJoinedDTO {
  roomId: string;
  participantId: string;
  token: string;
  role: ParticipantRole;
}

export interface RoomAvailabilityDTO {
  available: boolean;
  reason?: string;
}

export interface HostRoomViewDTO {
  roomId: string;
  roomCode: string;
  title: string | null;
  status: RoomStatus;
  currentRoundNumber: number;
  playerCount: number;
  maxPlayers: number;
  locked: boolean;
  isOwner: true;
  expiresAt: Date;
}

export interface PlayerRoomViewDTO {
  roomId: string;
  roomCode: string;
  title: string | null;
  status: RoomStatus;
  currentRoundNumber: number;
  playerCount: number;
  maxPlayers: number;
  locked: boolean;
  isOwner: false;
  hostDisplayName: string;
  expiresAt: Date;
}
