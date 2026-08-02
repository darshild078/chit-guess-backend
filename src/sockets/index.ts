import { Server } from 'socket.io';
import { Server as HttpServer } from 'http';
import { corsOptions } from '../config/cors.js';
import { socketAuthMiddleware } from './auth.js';
import { handleRoomConnection } from './handlers/room.handler.js';
import { handleSubmissionEvents } from './handlers/submission.handler.js';
import { handleInboxEvents } from './handlers/inbox.handler.js';
import { ServerToClientEvents, ClientToServerEvents, InterServerEvents, SocketData } from '../types/socket.types.js';

export function initializeSockets(httpServer: HttpServer) {
  const io = new Server<ClientToServerEvents, ServerToClientEvents, InterServerEvents, SocketData>(httpServer, {
    cors: corsOptions,
  });

  io.use(socketAuthMiddleware as any);

  io.on('connection', async (socket) => {
    await handleRoomConnection(io, socket);
    handleSubmissionEvents(io, socket);
    handleInboxEvents(io, socket);
  });

  return io;
}
