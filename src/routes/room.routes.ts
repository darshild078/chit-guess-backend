import { Router } from 'express';
import { roomController } from '../controllers/room.controller.js';
import { authMiddleware } from '../middleware/auth.middleware.js';
import { ownerMiddleware } from '../middleware/owner.middleware.js';
import { roomMemberMiddleware } from '../middleware/room-member.middleware.js';
import { joinLimiter, generalLimiter } from '../middleware/rate-limit.middleware.js';
import { validate } from '../middleware/validate.middleware.js';
import { createRoomSchema, joinRoomSchema, roomCodeParamSchema } from '../validators/room.validator.js';
import { z } from 'zod';

export const roomRoutes = Router();

roomRoutes.post('/', joinLimiter, validate(createRoomSchema), roomController.createRoom);
roomRoutes.post('/join', joinLimiter, validate(joinRoomSchema), roomController.joinRoom);

roomRoutes.get('/code/:roomCode/availability', validate(roomCodeParamSchema, 'params'), roomController.checkAvailability);

roomRoutes.use(authMiddleware);

roomRoutes.get('/current', roomController.getCurrentRoom);

// All these routes require room membership
roomRoutes.use('/:roomId', roomMemberMiddleware);

roomRoutes.post('/:roomId/leave', roomController.leaveRoom);
roomRoutes.get('/:roomId/activity', roomController.getActivity);

// Owner only routes
roomRoutes.post('/:roomId/rounds', ownerMiddleware, roomController.startRound);
roomRoutes.post('/:roomId/submissions/open', ownerMiddleware, roomController.openSubmissions);
roomRoutes.post('/:roomId/submissions/close', ownerMiddleware, roomController.closeSubmissions);
roomRoutes.post('/:roomId/aliases/shuffle', ownerMiddleware, roomController.shuffleAliases);
roomRoutes.post('/:roomId/reveal', ownerMiddleware, roomController.revealIdentities);
roomRoutes.post('/:roomId/players/:aliasId/remove', ownerMiddleware, roomController.removePlayer);
roomRoutes.post('/:roomId/lock', ownerMiddleware, validate(z.object({ locked: z.boolean() })), roomController.lockRoom);
roomRoutes.post('/:roomId/end', ownerMiddleware, roomController.endRoom);
