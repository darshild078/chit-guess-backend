import { Router } from 'express';
import { healthRoutes } from './health.routes.js';
import { roomRoutes } from './room.routes.js';
import { submissionRoutes } from './submission.routes.js';
import { inboxRoutes } from './inbox.routes.js';
import { inboxController } from '../controllers/inbox.controller.js';
import { authMiddleware } from '../middleware/auth.middleware.js';
import { roomMemberMiddleware } from '../middleware/room-member.middleware.js';

export const apiRouter = Router();

apiRouter.use('/health', healthRoutes);
apiRouter.use('/rooms', roomRoutes);
apiRouter.use('/rooms/:roomId/submission', submissionRoutes);
apiRouter.use('/rooms/:roomId/inbox', inboxRoutes);

// Move results route here due to params setup
const resultRoutes = Router({ mergeParams: true });
resultRoutes.use(authMiddleware, roomMemberMiddleware);
resultRoutes.get('/', inboxController.getResults);
apiRouter.use('/rooms/:roomId/results', resultRoutes);
