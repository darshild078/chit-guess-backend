import { describe, it, expect } from 'vitest';
import { makeAuthRequest, createFullTestRoom } from '../helpers/test-helpers.js';

describe('Inbox Operations', () => {
  it('Should return anonymous inbox with aliases', async () => {
    const { roomId, ownerToken, arthurToken } = await createFullTestRoom();
    await makeAuthRequest('post', `/api/v1/rooms/${roomId}/rounds`, ownerToken);
    await makeAuthRequest('post', `/api/v1/rooms/${roomId}/submissions/open`, ownerToken);
    
    await makeAuthRequest('post', `/api/v1/rooms/${roomId}/submission`, arthurToken, { body: 'My secret chit' });
    await makeAuthRequest('post', `/api/v1/rooms/${roomId}/submissions/close`, ownerToken);
    
    const res = await makeAuthRequest('get', `/api/v1/rooms/${roomId}/inbox/anonymous`, ownerToken);
    
    expect(res.status).toBe(200);
    expect(res.body.data.chits).toHaveLength(1);
    expect(res.body.data.chits[0].body).toBe('My secret chit');
    expect(res.body.data.chits[0].alias).toMatch(/Player \d/);
    expect(res.body.data.chits[0].anonymousChitId).toBeDefined();
  });

  it('Should shuffle aliases (new epoch, new opaque IDs)', async () => {
    const { roomId, ownerToken, arthurToken } = await createFullTestRoom();
    await makeAuthRequest('post', `/api/v1/rooms/${roomId}/rounds`, ownerToken);
    await makeAuthRequest('post', `/api/v1/rooms/${roomId}/submissions/open`, ownerToken);
    await makeAuthRequest('post', `/api/v1/rooms/${roomId}/submission`, arthurToken, { body: 'Hello' });
    await makeAuthRequest('post', `/api/v1/rooms/${roomId}/submissions/close`, ownerToken);
    
    const before = await makeAuthRequest('get', `/api/v1/rooms/${roomId}/inbox/anonymous`, ownerToken);
    const beforeId = before.body.data.chits[0].anonymousChitId;
    const beforeEpoch = before.body.data.aliasEpoch;

    await makeAuthRequest('post', `/api/v1/rooms/${roomId}/aliases/shuffle`, ownerToken);
    
    const after = await makeAuthRequest('get', `/api/v1/rooms/${roomId}/inbox/anonymous`, ownerToken);
    const afterId = after.body.data.chits[0].anonymousChitId;
    const afterEpoch = after.body.data.aliasEpoch;

    expect(afterEpoch).toBeGreaterThan(beforeEpoch);
    expect(afterId).not.toBe(beforeId);
  });
});
