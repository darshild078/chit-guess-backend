import { app } from '../../src/app.js';
// @ts-ignore
import request from 'supertest';

export async function makeAuthRequest(method: 'get' | 'post' | 'patch' | 'delete', path: string, token: string, body?: any) {
  let req = request(app)[method](path).set('Authorization', `Bearer ${token}`);
  if (body) {
    req = req.send(body);
  }
  return req;
}

export async function createTestRoom(hostDisplayName: string) {
  const res = await request(app)
    .post('/api/v1/rooms')
    .send({ hostDisplayName, maxPlayers: 10 });
  
  return {
    roomId: res.body.data.roomId,
    roomCode: res.body.data.roomCode,
    ownerToken: res.body.data.token,
    participantId: res.body.data.participantId,
  };
}

export async function joinTestRoom(roomCode: string, displayName: string) {
  const res = await request(app)
    .post('/api/v1/rooms/join')
    .send({ roomCode, displayName });
  
  return {
    participantId: res.body.data.participantId,
    token: res.body.data.token,
  };
}

export async function createFullTestRoom() {
  const { roomId, roomCode, ownerToken, participantId: ownerId } = await createTestRoom('John');
  
  const { token: arthurToken, participantId: arthurId } = await joinTestRoom(roomCode, 'Arthur');
  const { token: sadieToken, participantId: sadieId } = await joinTestRoom(roomCode, 'Sadie');

  return {
    roomId,
    roomCode,
    ownerToken,
    ownerId,
    arthurToken,
    arthurId,
    sadieToken,
    sadieId
  };
}
