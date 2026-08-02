import { Router } from 'express';
import { inboxController } from '../controllers/inbox.controller.js';
import { authMiddleware } from '../middleware/auth.middleware.js';
import { roomMemberMiddleware } from '../middleware/room-member.middleware.js';
import { validate } from '../middleware/validate.middleware.js';
import { markReadSchema, markGuessSchema } from '../validators/inbox.validator.js';

export const inboxRoutes = Router({ mergeParams: true });

inboxRoutes.use(authMiddleware);
inboxRoutes.use(roomMemberMiddleware);

inboxRoutes.get('/anonymous', inboxController.getAnonymousInbox);
inboxRoutes.patch('/:anonymousChitId/read', validate(markReadSchema), inboxController.markRead);
inboxRoutes.patch('/:anonymousChitId/guess', validate(markGuessSchema), inboxController.markGuessed);
