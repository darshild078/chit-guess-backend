process.env.PORT = process.env.PORT || '5000';
process.env.DATABASE_URL = process.env.DATABASE_URL || 'postgresql://chitguess:chitguess_dev_password@localhost:5432/chitguess';
process.env.JWT_SECRET = process.env.JWT_SECRET || 'test-super-secret-jwt-key';
process.env.FRONTEND_URL = process.env.FRONTEND_URL || 'http://localhost:5173';
process.env.NODE_ENV = 'test';

import { beforeAll, afterAll, beforeEach } from 'vitest';
import { prisma } from '../src/config/prisma.js';

// Setup before all tests
beforeAll(async () => {
  // Wait for db connection if needed
});

// Teardown after all tests
afterAll(async () => {
  await prisma.$disconnect();
});

// Clean up DB before each test
beforeEach(async () => {
  try {
    // Clear tables
    await prisma.chitMessage.deleteMany();
    await prisma.roundAlias.deleteMany();
    await prisma.gameRound.deleteMany();
    await prisma.participant.deleteMany();
    await prisma.room.deleteMany();
  } catch (err) {
    // Ignore cleanup errors if DB not running
  }
});
