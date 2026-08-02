import { describe, it, expect } from 'vitest';
import { app } from '../../src/app.js';
// @ts-ignore
import request from 'supertest';
import { createTestRoom, joinTestRoom, makeAuthRequest, createFullTestRoom } from '../helpers/test-helpers.js';

describe('Room Operations', () => {
  it('Should create a room with valid data', async () => {
    const res = await request(app)
      .post('/api/v1/rooms')
      .send({ hostDisplayName: 'John', maxPlayers: 5 });
    
    expect(res.status).toBe(201);
    expect(res.body.success).toBe(true);
    expect(res.body.data.roomCode).toBeDefined();
    expect(res.body.data.token).toBeDefined();
  });

  it('Should reject room creation with short display name', async () => {
    const res = await request(app)
      .post('/api/v1/rooms')
      .send({ hostDisplayName: 'J', maxPlayers: 5 });
    
    expect(res.status).toBe(400);
    expect(res.body.success).toBe(false);
  });

  it('Should generate a 6-char room code', async () => {
    const res = await request(app)
      .post('/api/v1/rooms')
      .send({ hostDisplayName: 'John', maxPlayers: 5 });
    
    expect(res.body.data.roomCode).toHaveLength(6);
  });

  it('Should join a room with valid code', async () => {
    const { roomCode } = await createTestRoom('John');
    
    const res = await request(app)
      .post('/api/v1/rooms/join')
      .send({ roomCode, displayName: 'Arthur' });
    
    expect(res.status).toBe(200);
    expect(res.body.data.token).toBeDefined();
  });

  it('Should reject duplicate display names in same room', async () => {
    const { roomCode } = await createTestRoom('John');
    
    await request(app)
      .post('/api/v1/rooms/join')
      .send({ roomCode, displayName: 'Arthur' });
      
    const res = await request(app)
      .post('/api/v1/rooms/join')
      .send({ roomCode, displayName: 'Arthur' });
      
    expect(res.status).toBe(409);
  });

  it('Should reject joining a full room', async () => {
    const res = await request(app)
      .post('/api/v1/rooms')
      .send({ hostDisplayName: 'John', maxPlayers: 2 });
    
    const roomCode = res.body.data.roomCode;
    
    await request(app).post('/api/v1/rooms/join').send({ roomCode, displayName: 'Arthur' });
    const fullRes = await request(app).post('/api/v1/rooms/join').send({ roomCode, displayName: 'Sadie' });
    
    expect(fullRes.status).toBe(403);
  });

  it('Should return different views for owner vs player', async () => {
    const { roomId, ownerToken, arthurToken } = await createFullTestRoom();
    
    const ownerRes = await makeAuthRequest('get', '/api/v1/rooms/current', ownerToken);
    expect(ownerRes.status).toBe(200);
    expect(ownerRes.body.data.isOwner).toBe(true);
    expect(ownerRes.body.data.hostDisplayName).toBeUndefined(); // Owner room view should NOT contain hostDisplayName field
    
    const playerRes = await makeAuthRequest('get', '/api/v1/rooms/current', arthurToken);
    expect(playerRes.status).toBe(200);
    expect(playerRes.body.data.isOwner).toBe(false);
    expect(playerRes.body.data.hostDisplayName).toBe('John'); // Player room view should contain hostDisplayName
  });
});
