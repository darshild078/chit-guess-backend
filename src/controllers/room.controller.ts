import { Request, Response, NextFunction } from 'express';
import { roomService } from '../services/room.service.js';
import { roundService } from '../services/round.service.js';
import { participantService } from '../services/participant.service.js';
import { revealService } from '../services/reveal.service.js';
import { aliasService } from '../services/alias.service.js';
import { io } from '../server.js';
import { emitRoomStateUpdated, emitRoundStarted, emitPlayerActivityUpdated } from '../sockets/emitters/room.emitter.js';

export const roomController = {
  async createRoom(req: Request, res: Response, next: NextFunction) {
    try {
      const { hostDisplayName, title, maxPlayers } = req.body;
      const result = await roomService.createRoom(hostDisplayName, title, maxPlayers);
      res.status(201).json({ success: true, data: result });
    } catch (error) { next(error); }
  },

  async joinRoom(req: Request, res: Response, next: NextFunction) {
    try {
      const { roomCode, displayName } = req.body;
      const result = await roomService.joinRoom(roomCode, displayName);
      
      // Broadcast realtime updates when a player joins
      await emitRoomStateUpdated(io, result.roomId);
      await emitPlayerActivityUpdated(io, result.roomId);

      res.json({ success: true, data: result });
    } catch (error) { next(error); }
  },

  async checkAvailability(req: Request, res: Response, next: NextFunction) {
    try {
      const { roomCode } = req.params;
      const result = await roomService.checkAvailability(roomCode as string);
      res.json({ success: true, data: result });
    } catch (error) { next(error); }
  },

  async getCurrentRoom(req: Request, res: Response, next: NextFunction) {
    try {
      const { participantId, roomId, role } = req.participant!;
      const result = await roomService.getRoomView(participantId, roomId, role);
      res.json({ success: true, data: result });
    } catch (error) { next(error); }
  },

  async leaveRoom(req: Request, res: Response, next: NextFunction) {
    try {
      const { participantId, roomId } = req.participant!;
      await roomService.leaveRoom(participantId);

      await emitRoomStateUpdated(io, roomId);
      await emitPlayerActivityUpdated(io, roomId);

      res.json({ success: true, data: null });
    } catch (error) { next(error); }
  },

  async lockRoom(req: Request, res: Response, next: NextFunction) {
    try {
      const { roomId } = req.participant!;
      const { locked } = req.body;
      await roomService.lockRoom(roomId, locked);
      await emitRoomStateUpdated(io, roomId);
      res.json({ success: true, data: null });
    } catch (error) { next(error); }
  },

  async endRoom(req: Request, res: Response, next: NextFunction) {
    try {
      const { roomId } = req.participant!;
      await roomService.endRoom(roomId);
      await emitRoomStateUpdated(io, roomId);
      res.json({ success: true, data: null });
    } catch (error) { next(error); }
  },

  async startRound(req: Request, res: Response, next: NextFunction) {
    try {
      const { roomId } = req.participant!;
      const round = await roundService.startRound(roomId);
      await emitRoomStateUpdated(io, roomId);
      emitRoundStarted(io, roomId, round.roundNumber);
      res.json({ success: true, data: round });
    } catch (error) { next(error); }
  },

  async openSubmissions(req: Request, res: Response, next: NextFunction) {
    try {
      const { roomId } = req.participant!;
      await roundService.openSubmissions(roomId);
      await emitRoomStateUpdated(io, roomId);
      res.json({ success: true, data: null });
    } catch (error) { next(error); }
  },

  async closeSubmissions(req: Request, res: Response, next: NextFunction) {
    try {
      const { roomId } = req.participant!;
      await roundService.closeSubmissions(roomId);
      await emitRoomStateUpdated(io, roomId);
      res.json({ success: true, data: null });
    } catch (error) { next(error); }
  },

  async shuffleAliases(req: Request, res: Response, next: NextFunction) {
    try {
      const { roomId } = req.participant!;
      const round = await roundService.getCurrentRound(roomId);
      if (round) {
        await aliasService.reshuffleAliases(round.id);
        await emitPlayerActivityUpdated(io, roomId);
      }
      res.json({ success: true, data: null });
    } catch (error) { next(error); }
  },

  async revealIdentities(req: Request, res: Response, next: NextFunction) {
    try {
      const { roomId } = req.participant!;
      const results = await revealService.revealIdentities(roomId);
      await emitRoomStateUpdated(io, roomId);
      io.to(`room:${roomId}`).emit('room:identities-revealed', results);
      res.json({ success: true, data: results });
    } catch (error) { next(error); }
  },

  async removePlayer(req: Request, res: Response, next: NextFunction) {
    try {
      const { roomId } = req.participant!;
      const { aliasId } = req.params;
      await participantService.removePlayer(roomId, aliasId as string);
      res.json({ success: true, data: null });
    } catch (error) { next(error); }
  },

  async getActivity(req: Request, res: Response, next: NextFunction) {
    try {
      const { roomId, participantId, role } = req.participant!;
      const activity = await participantService.getPlayerActivity(roomId, participantId, role);
      res.json({ success: true, data: activity });
    } catch (error) { next(error); }
  }
};
