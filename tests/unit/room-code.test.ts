import { describe, it, expect } from 'vitest';
import { generateRoomCode } from '../../src/utils/room-code.js';

describe('Room Code Generator', () => {
  it('Should generate 6-character codes', () => {
    const code = generateRoomCode();
    expect(code).toHaveLength(6);
  });

  it('Should only use allowed characters (no O, 0, I, 1)', () => {
    const code = generateRoomCode();
    expect(code).toMatch(/^[ABCDEFGHJKLMNPQRSTUVWXYZ23456789]+$/);
  });

  it('Should generate unique codes across multiple calls', () => {
    const code1 = generateRoomCode();
    const code2 = generateRoomCode();
    // While there's a tiny chance of collision, it's virtually impossible for 2 immediate calls
    expect(code1).not.toBe(code2);
  });
});
