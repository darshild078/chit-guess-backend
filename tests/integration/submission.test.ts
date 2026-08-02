import { describe, it, expect } from 'vitest';
import { makeAuthRequest, createFullTestRoom } from '../helpers/test-helpers.js';

describe('Submission Operations', () => {
  it('Should submit a chit when submissions are open', async () => {
    const { roomId, ownerToken, arthurToken } = await createFullTestRoom();
    await makeAuthRequest('post', `/api/v1/rooms/${roomId}/rounds`, ownerToken);
    await makeAuthRequest('post', `/api/v1/rooms/${roomId}/submissions/open`, ownerToken);
    
    const res = await makeAuthRequest('post', `/api/v1/rooms/${roomId}/submission`, arthurToken, { body: 'Hello World' });
    expect(res.status).toBe(201);
  });

  it('Should reject submission when submissions are closed', async () => {
    const { roomId, ownerToken, arthurToken } = await createFullTestRoom();
    await makeAuthRequest('post', `/api/v1/rooms/${roomId}/rounds`, ownerToken);
    
    const res = await makeAuthRequest('post', `/api/v1/rooms/${roomId}/submission`, arthurToken, { body: 'Hello World' });
    expect(res.status).toBe(403);
  });

  it('Should edit a chit when submissions are open', async () => {
    const { roomId, ownerToken, arthurToken } = await createFullTestRoom();
    await makeAuthRequest('post', `/api/v1/rooms/${roomId}/rounds`, ownerToken);
    await makeAuthRequest('post', `/api/v1/rooms/${roomId}/submissions/open`, ownerToken);
    
    await makeAuthRequest('post', `/api/v1/rooms/${roomId}/submission`, arthurToken, { body: 'Hello' });
    const res = await makeAuthRequest('patch', `/api/v1/rooms/${roomId}/submission`, arthurToken, { body: 'Updated' });
    expect(res.status).toBe(200);
  });

  it('Should reject duplicate submission for same round', async () => {
    const { roomId, ownerToken, arthurToken } = await createFullTestRoom();
    await makeAuthRequest('post', `/api/v1/rooms/${roomId}/rounds`, ownerToken);
    await makeAuthRequest('post', `/api/v1/rooms/${roomId}/submissions/open`, ownerToken);
    
    await makeAuthRequest('post', `/api/v1/rooms/${roomId}/submission`, arthurToken, { body: 'Hello' });
    const res = await makeAuthRequest('post', `/api/v1/rooms/${roomId}/submission`, arthurToken, { body: 'World' });
    expect(res.status).toBe(409);
  });

  it('Should enforce max 200 char body', async () => {
    const { roomId, ownerToken, arthurToken } = await createFullTestRoom();
    await makeAuthRequest('post', `/api/v1/rooms/${roomId}/rounds`, ownerToken);
    await makeAuthRequest('post', `/api/v1/rooms/${roomId}/submissions/open`, ownerToken);
    
    const longBody = 'A'.repeat(201);
    const res = await makeAuthRequest('post', `/api/v1/rooms/${roomId}/submission`, arthurToken, { body: longBody });
    expect(res.status).toBe(400);
  });
});
