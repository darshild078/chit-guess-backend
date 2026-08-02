import { Socket, Server } from 'socket.io';
import { submissionService } from '../../services/submission.service.js';
import { emitPlayerActivityUpdated } from '../emitters/room.emitter.js';
import { ServerToClientEvents, ClientToServerEvents, InterServerEvents, SocketData } from '../../types/socket.types.js';

type IOSocket = Socket<ClientToServerEvents, ServerToClientEvents, InterServerEvents, SocketData>;
type IOServer = Server<ClientToServerEvents, ServerToClientEvents, InterServerEvents, SocketData>;

export function handleSubmissionEvents(io: IOServer, socket: IOSocket) {
  const { participantId, roomId } = socket.data;

  socket.on('submission:submit', async (data, callback) => {
    try {
      await submissionService.submitChit(participantId, roomId, data.body);
      await emitPlayerActivityUpdated(io, roomId);
      callback({ success: true });
    } catch (error: any) {
      callback({ success: false, error: error.message });
    }
  });

  socket.on('submission:edit', async (data, callback) => {
    try {
      await submissionService.editChit(participantId, roomId, data.body);
      callback({ success: true });
    } catch (error: any) {
      callback({ success: false, error: error.message });
    }
  });

  socket.on('submission:delete', async (callback) => {
    try {
      await submissionService.deleteChit(participantId, roomId);
      await emitPlayerActivityUpdated(io, roomId);
      callback({ success: true });
    } catch (error: any) {
      callback({ success: false, error: error.message });
    }
  });
}
