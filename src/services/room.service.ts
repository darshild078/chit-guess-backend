import { roomRepository } from '../repositories/room.repository.js';
import { participantRepository } from '../repositories/participant.repository.js';
import { AppError } from '../errors/app-error.js';
import { ERROR_CODES } from '../errors/error-codes.js';
import { ParticipantRole, RoomStatus } from '../types/enums.js';
import { generateRoomCode } from '../utils/room-code.js';
import { env } from '../config/env.js';
import { sessionService } from './session.service.js';
import { prisma } from '../config/prisma.js';
import { RoomCreatedDTO, RoomJoinedDTO, RoomAvailabilityDTO, HostRoomViewDTO, PlayerRoomViewDTO } from '../dto/room.dto.js';

export const roomService = {
  async createRoom(hostDisplayName: string, title?: string, maxPlayers = 10): Promise<RoomCreatedDTO> {
    let roomCode = generateRoomCode();
    
    // Ensure unique code
    let retries = 5;
    while (retries > 0) {
      const existing = await roomRepository.findByCode(roomCode);
      if (!existing) break;
      roomCode = generateRoomCode();
      retries--;
    }

    if (retries === 0) {
      throw AppError.internalError(ERROR_CODES.INTERNAL_SERVER_ERROR, 'Could not generate unique room code');
    }

    const expiresAt = new Date(Date.now() + env.ROOM_EXPIRY_HOURS * 60 * 60 * 1000);

    const result = await prisma.$transaction(async (tx) => {
      const room = await tx.room.create({
        data: {
          code: roomCode,
          title,
          maxPlayers,
          expiresAt,
        },
      });

      const participant = await tx.participant.create({
        data: {
          roomId: room.id,
          displayName: hostDisplayName,
          role: ParticipantRole.owner,
        },
      });

      await tx.room.update({
        where: { id: room.id },
        data: { ownerParticipantId: participant.id },
      });

      return { room, participant };
    });

    const token = sessionService.createSession({
      participantId: result.participant.id,
      roomId: result.room.id,
      role: ParticipantRole.owner,
      sessionVersion: 1,
    });

    return {
      roomId: result.room.id,
      roomCode: result.room.code,
      participantId: result.participant.id,
      token,
      role: ParticipantRole.owner,
    };
  },

  async joinRoom(roomCode: string, displayName: string): Promise<RoomJoinedDTO> {
    const room = await roomRepository.findByCode(roomCode);
    if (!room) throw AppError.notFound(ERROR_CODES.ROOM_NOT_FOUND, 'Room not found');
    if (room.status === RoomStatus.ended) throw AppError.forbidden(ERROR_CODES.ROOM_ENDED, 'Room has ended');
    if (room.expiresAt < new Date()) throw AppError.forbidden(ERROR_CODES.ROOM_EXPIRED, 'Room has expired');
    if (room.locked) throw AppError.forbidden(ERROR_CODES.ROOM_LOCKED, 'Room is locked');

    const participantCount = room._count.participants;
    if (participantCount >= room.maxPlayers) {
      throw AppError.forbidden(ERROR_CODES.ROOM_FULL, 'Room is full');
    }

    const existing = await participantRepository.findByRoomIdAndName(room.id, displayName);
    if (existing) {
      if (!existing.removed) {
        throw AppError.conflict(ERROR_CODES.DUPLICATE_NAME, 'Display name already taken in this room');
      }
      // Delete old removed participant record so unique constraint is satisfied
      await prisma.participant.delete({ where: { id: existing.id } });
    }

    const participant = await participantRepository.create({
      roomId: room.id,
      displayName,
      role: ParticipantRole.player,
    });

    const token = sessionService.createSession({
      participantId: participant.id,
      roomId: room.id,
      role: ParticipantRole.player,
      sessionVersion: 1,
    });

    return {
      roomId: room.id,
      participantId: participant.id,
      token,
      role: ParticipantRole.player,
    };
  },

  async checkAvailability(roomCode: string): Promise<RoomAvailabilityDTO> {
    const room = await roomRepository.findByCode(roomCode);
    if (!room) return { available: false, reason: 'Room not found' };
    if (room.status === RoomStatus.ended) return { available: false, reason: 'Room has ended' };
    if (room.expiresAt < new Date()) return { available: false, reason: 'Room has expired' };
    if (room.locked) return { available: false, reason: 'Room is locked' };
    if (room._count.participants >= room.maxPlayers) return { available: false, reason: 'Room is full' };

    return { available: true };
  },

  async getRoomView(participantId: string, roomId: string, role: ParticipantRole): Promise<HostRoomViewDTO | PlayerRoomViewDTO> {
    const room = await roomRepository.findById(roomId);
    if (!room) throw AppError.notFound(ERROR_CODES.ROOM_NOT_FOUND, 'Room not found');

    const playerCount = await participantRepository.countActiveByRoom(roomId);

    if (role === ParticipantRole.owner) {
      return {
        roomId: room.id,
        roomCode: room.code,
        title: room.title,
        status: room.status,
        currentRoundNumber: room.currentRoundNumber,
        playerCount,
        maxPlayers: room.maxPlayers,
        locked: room.locked,
        isOwner: true,
        expiresAt: room.expiresAt,
      };
    } else {
      const owner = room.ownerParticipantId ? await participantRepository.findById(room.ownerParticipantId) : null;
      return {
        roomId: room.id,
        roomCode: room.code,
        title: room.title,
        status: room.status,
        currentRoundNumber: room.currentRoundNumber,
        playerCount,
        maxPlayers: room.maxPlayers,
        locked: room.locked,
        isOwner: false,
        hostDisplayName: owner?.displayName || 'Host',
        expiresAt: room.expiresAt,
      };
    }
  },

  async leaveRoom(participantId: string): Promise<void> {
    await participantRepository.updateConnected(participantId, false);
  },

  async lockRoom(roomId: string, locked: boolean): Promise<void> {
    await roomRepository.updateLocked(roomId, locked);
  },

  async endRoom(roomId: string): Promise<void> {
    await roomRepository.updateStatus(roomId, RoomStatus.ended);
  },
};
