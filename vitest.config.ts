import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'node',
    setupFiles: ['./tests/setup.ts'],
    env: {
      PORT: '5000',
      DATABASE_URL: 'postgresql://chitguess:chitguess_dev_password@localhost:5432/chitguess',
      JWT_SECRET: 'test-super-secret-jwt-key',
      FRONTEND_URL: 'http://localhost:5173',
      NODE_ENV: 'test',
    },
  },
});
