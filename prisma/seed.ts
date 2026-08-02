import { PrismaClient } from '@prisma/client';
import { ParticipantRole, RoomStatus, RoundStatus } from '../src/types/enums.js';

const prisma = new PrismaClient();

async function main() {
  console.log('Seeding database...');

  // Clean DB
  await prisma.chitMessage.deleteMany();
  await prisma.roundAlias.deleteMany();
  await prisma.gameRound.deleteMany();
  await prisma.participant.deleteMany();
  await prisma.room.deleteMany();

  // Create Room
  const room = await prisma.room.create({
    data: {
      code: 'K7MP4X',
      title: 'Test Game Room',
      status: RoomStatus.waiting,
      maxPlayers: 10,
      currentRoundNumber: 1,
      expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000),
    }
  });

  // Create Participants
  const john = await prisma.participant.create({
    data: {
      roomId: room.id,
      displayName: 'John',
      role: ParticipantRole.owner,
      connected: true,
    }
  });

  await prisma.room.update({
    where: { id: room.id },
    data: { ownerParticipantId: john.id }
  });

  const arthur = await prisma.participant.create({
    data: {
      roomId: room.id,
      displayName: 'Arthur',
      role: ParticipantRole.player,
      connected: true,
    }
  });

  const sadie = await prisma.participant.create({
    data: {
      roomId: room.id,
      displayName: 'Sadie',
      role: ParticipantRole.player,
      connected: true,
    }
  });

  // Create Round
  const round = await prisma.gameRound.create({
    data: {
      roomId: room.id,
      roundNumber: 1,
      status: RoundStatus.submissions_closed,
      aliasEpoch: 1,
    }
  });

  // Create Chits
  await prisma.chitMessage.create({
    data: {
      roomId: room.id,
      roundId: round.id,
      senderId: arthur.id,
      body: 'Hello',
    }
  });

  await prisma.chitMessage.create({
    data: {
      roomId: room.id,
      roundId: round.id,
      senderId: sadie.id,
      body: 'World',
    }
  });

  // Create Aliases
  await prisma.roundAlias.createMany({
    data: [
      {
        roundId: round.id,
        aliasEpoch: 1,
        participantId: arthur.id,
        aliasNumber: 1,
        opaqueAliasId: 'opaque-arthur-id'
      },
      {
        roundId: round.id,
        aliasEpoch: 1,
        participantId: sadie.id,
        aliasNumber: 2,
        opaqueAliasId: 'opaque-sadie-id'
      }
    ]
  });

  console.log('Seed data created successfully:');
  console.log(`Room Code: ${room.code}`);
  console.log(`Owner: John`);
  console.log(`Players: Arthur, Sadie`);
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
