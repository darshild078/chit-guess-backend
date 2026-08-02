import { describe, it, expect } from 'vitest';
import { makeAuthRequest, createFullTestRoom } from '../helpers/test-helpers.js';

describe('Reveal Operations', () => {
  it('Should reveal identities for current round', async () => {
    const { roomId, ownerToken, arthurToken, sadieToken } = await createFullTestRoom();
    
    await makeAuthRequest('post', `/api/v1/rooms/${roomId}/rounds`, ownerToken);
    await makeAuthRequest('post', `/api/v1/rooms/${roomId}/submissions/open`, ownerToken);
    
    await makeAuthRequest('post', `/api/v1/rooms/${roomId}/submission`, arthurToken, { body: 'Arthur chit' });
    await makeAuthRequest('post', `/api/v1/rooms/${roomId}/submission`, sadieToken, { body: 'Sadie chit' });
    
    await makeAuthRequest('post', `/api/v1/rooms/${roomId}/submissions/close`, ownerToken);
    
    const res = await makeAuthRequest('post', `/api/v1/rooms/${roomId}/reveal`, ownerToken);
    
    expect(res.status).toBe(200);
    const chits = res.body.data.chits;
    
    expect(chits).toHaveLength(2);
    expect(chits.find((c: any) => c.senderDisplayName === 'Arthur')).toBeDefined();
    expect(chits.find((c: any) => c.senderDisplayName === 'Sadie')).toBeDefined();
  });

  it('Should reject reveal if already revealed', async () => {
    const { roomId, ownerToken, arthurToken } = await createFullTestRoom();
    
    await makeAuthRequest('post', `/api/v1/rooms/${roomId}/rounds`, ownerToken);
    await makeAuthRequest('post', `/api/v1/rooms/${roomId}/submissions/open`, ownerToken);
    await makeAuthRequest('post', `/api/v1/rooms/${roomId}/submission`, arthurToken, { body: 'Arthur chit' });
    await makeAuthRequest('post', `/api/v1/rooms/${roomId}/submissions/close`, ownerToken);
    
    await makeAuthRequest('post', `/api/v1/rooms/${roomId}/reveal`, ownerToken);
    const res = await makeAuthRequest('post', `/api/v1/rooms/${roomId}/reveal`, ownerToken);
    
    expect(res.status).toBe(409);
  });
});
