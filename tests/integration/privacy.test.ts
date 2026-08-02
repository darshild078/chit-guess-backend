import { describe, it, expect, beforeAll } from 'vitest';
import { makeAuthRequest, createFullTestRoom } from '../helpers/test-helpers.js';

describe('Privacy Tests', () => {
  let roomId: string;
  let ownerToken: string;
  let arthurToken: string;
  let sadieToken: string;
  let arthurId: string;
  let sadieId: string;

  beforeAll(async () => {
    const data = await createFullTestRoom();
    roomId = data.roomId;
    ownerToken = data.ownerToken;
    arthurToken = data.arthurToken;
    sadieToken = data.sadieToken;
    arthurId = data.arthurId;
    sadieId = data.sadieId;

    await makeAuthRequest('post', `/api/v1/rooms/${roomId}/rounds`, ownerToken);
    await makeAuthRequest('post', `/api/v1/rooms/${roomId}/submissions/open`, ownerToken);
    await makeAuthRequest('post', `/api/v1/rooms/${roomId}/submission`, arthurToken, { body: 'Hello' });
    await makeAuthRequest('post', `/api/v1/rooms/${roomId}/submission`, sadieToken, { body: 'World' });
    await makeAuthRequest('post', `/api/v1/rooms/${roomId}/submissions/close`, ownerToken);
  });

  describe('Host Anonymous API', () => {
    it('should NOT contain real player names in anonymous inbox', async () => {
      const response = await makeAuthRequest('get', `/api/v1/rooms/${roomId}/inbox/anonymous`, ownerToken);
      const responseStr = JSON.stringify(response.body);
      expect(responseStr).not.toContain('Arthur');
      expect(responseStr).not.toContain('Sadie');
    });

    it('should NOT contain real participant IDs in anonymous inbox', async () => {
      const response = await makeAuthRequest('get', `/api/v1/rooms/${roomId}/inbox/anonymous`, ownerToken);
      const responseStr = JSON.stringify(response.body);
      expect(responseStr).not.toContain(arthurId);
      expect(responseStr).not.toContain(sadieId);
    });
  });

  describe('Host Activity API', () => {
    it('owner activity should NOT contain real player names', async () => {
      const response = await makeAuthRequest('get', `/api/v1/rooms/${roomId}/activity`, ownerToken);
      const responseStr = JSON.stringify(response.body);
      expect(responseStr).not.toContain('Arthur');
      expect(responseStr).not.toContain('Sadie');
    });

    it('owner activity should contain anonymous aliases', async () => {
      const response = await makeAuthRequest('get', `/api/v1/rooms/${roomId}/activity`, ownerToken);
      const data = response.body.data;
      expect(data.some((item: Record<string, unknown>) => typeof item.alias === 'string')).toBe(true);
    });
  });

  describe('Player API', () => {
    it('player activity should NOT contain message bodies', async () => {
      const response = await makeAuthRequest('get', `/api/v1/rooms/${roomId}/activity`, arthurToken);
      const responseStr = JSON.stringify(response.body);
      expect(responseStr).not.toContain('Hello');
      expect(responseStr).not.toContain('World');
    });

    it('player should see real display names in activity', async () => {
      const response = await makeAuthRequest('get', `/api/v1/rooms/${roomId}/activity`, arthurToken);
      const data = response.body.data;
      expect(data.some((item: Record<string, unknown>) => item.displayName === 'Sadie')).toBe(true);
    });

    it('player should only get own submission', async () => {
      const response = await makeAuthRequest('get', `/api/v1/rooms/${roomId}/submission`, arthurToken);
      expect(response.body.data.body).toBe('Hello');
    });
  });

  describe('Alias Reshuffling', () => {
    it('should generate different alias assignments after shuffle', async () => {
      const before = await makeAuthRequest('get', `/api/v1/rooms/${roomId}/inbox/anonymous`, ownerToken);
      await makeAuthRequest('post', `/api/v1/rooms/${roomId}/aliases/shuffle`, ownerToken);
      const after = await makeAuthRequest('get', `/api/v1/rooms/${roomId}/inbox/anonymous`, ownerToken);
      
      expect(after.body.data.aliasEpoch).not.toBe(before.body.data.aliasEpoch);
      
      const beforeIds = before.body.data.chits.map((c: Record<string, unknown>) => c.anonymousChitId);
      const afterIds = after.body.data.chits.map((c: Record<string, unknown>) => c.anonymousChitId);
      for (const id of beforeIds) {
        expect(afterIds).not.toContain(id);
      }
    });
  });

  describe('Post-Reveal', () => {
    it('should contain real names in revealed results', async () => {
      await makeAuthRequest('post', `/api/v1/rooms/${roomId}/reveal`, ownerToken);
      const response = await makeAuthRequest('get', `/api/v1/rooms/${roomId}/results`, ownerToken);
      const data = response.body.data;
      expect(data.chits.some((c: Record<string, unknown>) => c.senderDisplayName === 'Arthur')).toBe(true);
      expect(data.chits.some((c: Record<string, unknown>) => c.senderDisplayName === 'Sadie')).toBe(true);
    });
  });
});
