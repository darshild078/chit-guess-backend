import { Router } from 'express';
import { submissionController } from '../controllers/submission.controller.js';
import { authMiddleware } from '../middleware/auth.middleware.js';
import { roomMemberMiddleware } from '../middleware/room-member.middleware.js';
import { submissionLimiter } from '../middleware/rate-limit.middleware.js';
import { validate } from '../middleware/validate.middleware.js';
import { submitChitSchema, editChitSchema } from '../validators/submission.validator.js';

export const submissionRoutes = Router({ mergeParams: true });

submissionRoutes.use(authMiddleware);
submissionRoutes.use(roomMemberMiddleware);

submissionRoutes.get('/', submissionController.getSubmission);
submissionRoutes.post('/', submissionLimiter, validate(submitChitSchema), submissionController.submitChit);
submissionRoutes.patch('/', submissionLimiter, validate(editChitSchema), submissionController.editChit);
submissionRoutes.delete('/', submissionController.deleteChit);
