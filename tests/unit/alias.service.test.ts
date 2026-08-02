import { describe, it, expect, vi, beforeEach } from 'vitest';
import { aliasService } from '../../src/services/alias.service.js';
import { participantRepository } from '../../src/repositories/participant.repository.js';
import { roundRepository } from '../../src/repositories/round.repository.js';
import { prisma } from '../../src/config/prisma.js';
import { ParticipantRole } from '../../src/types/enums.js';

// Mock dependencies
vi.mock('../../src/repositories/participant.repository.js');
vi.mock('../../src/repositories/round.repository.js');
vi.mock('../../src/config/prisma.js', () => ({
  prisma: {
    $transaction: vi.fn(async (cb) => {
      return cb({
        roundAlias: {
          deleteMany: vi.fn(),
          createMany: vi.fn(),
        }
      });
    }),
  }
}));

describe('Alias Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('Should assign sequential alias numbers and random opaque IDs', async () => {
    const roundId = 'round-123';
    const roomId = 'room-123';
    
    vi.mocked(roundRepository.findById).mockResolvedValue({ id: roundId, roomId, aliasEpoch: 0 } as any);
    
    vi.mocked(participantRepository.findByRoomId).mockResolvedValue([
      { id: 'owner1', role: ParticipantRole.owner },
      { id: 'player1', role: ParticipantRole.player },
      { id: 'player2', role: ParticipantRole.player }
    ] as any);

    let createdData: any = null;
    vi.mocked(prisma.$transaction).mockImplementation(async (cb: any) => {
      const tx = {
        roundAlias: {
          deleteMany: vi.fn(),
          createMany: vi.fn((data: any) => {
            createdData = data.data;
          }),
        }
      };
      await cb(tx);
    });

    await aliasService.generateAliases(roundId, 0);

    expect(createdData).toHaveLength(2);
    
    const aliasNumbers = createdData.map((d: any) => d.aliasNumber).sort();
    expect(aliasNumbers).toEqual([1, 2]);

    expect(createdData.some((d: any) => d.participantId === 'owner1')).toBe(false);

    expect(createdData[0].opaqueAliasId).toBeDefined();
    expect(createdData[1].opaqueAliasId).toBeDefined();
    expect(createdData[0].opaqueAliasId).not.toBe(createdData[1].opaqueAliasId);
  });
});
