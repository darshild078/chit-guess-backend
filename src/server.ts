import http from 'http';
import { app } from './app.js';
import { env } from './config/env.js';
import { logger } from './config/logger.js';
import { initializeSockets } from './sockets/index.js';
import { prisma } from './config/prisma.js';

const httpServer = http.createServer(app);

export const io = initializeSockets(httpServer);

async function startServer() {
  try {
    await prisma.$connect();
    logger.info('Database connected successfully.');

    httpServer.listen(env.PORT, () => {
      logger.info(`Server running on port ${env.PORT} in ${env.NODE_ENV} mode.`);
    });
  } catch (error) {
    logger.error(error, 'Failed to start server');
    process.exit(1);
  }
}

// Global Process Crash Safety Nets
process.on('uncaughtException', (error) => {
  logger.error(error, 'CRITICAL: Uncaught Exception detected');
});

process.on('unhandledRejection', (reason) => {
  logger.error(reason, 'CRITICAL: Unhandled Promise Rejection detected');
});

function gracefulShutdown(signal: string) {
  logger.info(`Received ${signal}. Shutting down gracefully...`);
  httpServer.close(async () => {
    logger.info('HTTP server closed.');
    io.close();
    await prisma.$disconnect();
    logger.info('Database disconnected.');
    process.exit(0);
  });

  setTimeout(() => {
    logger.error('Could not close connections in time, forcefully shutting down');
    process.exit(1);
  }, 10000);
}

process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
process.on('SIGINT', () => gracefulShutdown('SIGINT'));

startServer();
