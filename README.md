# ChitGuess Backend

The backend for ChitGuess, built with Node.js, Express, Socket.IO, Prisma, and PostgreSQL.

## Setup Instructions

1. **Install dependencies**
   ```bash
   npm install
   ```

2. **Environment Variables**
   Create a `.env` file based on `.env.example`:
   ```env
   PORT=5000
   DATABASE_URL=postgresql://user:password@localhost:5432/chitguess
   JWT_SECRET=your_jwt_secret
   FRONTEND_URL=http://localhost:5173
   ```

3. **Database Setup**
   ```bash
   # Push schema to database
   npx prisma db push
   
   # Or run migrations
   npx prisma migrate dev
   
   # Seed the database for testing
   npm run db:seed
   ```

4. **Start Development Server**
   ```bash
   npm run dev
   ```

## Testing

Tests are written using Vitest. Make sure you have a test database running or configure the environment appropriately.

```bash
# Run tests
npm run test

# Run in watch mode
npm run test:watch
```

## API Summary

- `POST /api/v1/rooms` - Create a new room
- `POST /api/v1/rooms/join` - Join an existing room
- `GET /api/v1/rooms/current` - Get current room info
- `POST /api/v1/rooms/:roomId/rounds` - Start a new round (Owner)
- `POST /api/v1/rooms/:roomId/submissions/open` - Open submissions (Owner)
- `POST /api/v1/rooms/:roomId/submission` - Submit a chit (Player)
- `GET /api/v1/rooms/:roomId/inbox/anonymous` - Get anonymous inbox (Owner)

## Socket.IO Events

- `room:state-updated`: General room state updates
- `room:player-joined` / `room:player-left`: Participant connection status
- `room:player-activity-updated`: Activity indicators (who submitted)
- `submission:submit` (Client -> Server): Submit a chit

## Deployment

To deploy to Railway:
1. Connect GitHub repository
2. Set Environment variables (`DATABASE_URL`, `JWT_SECRET`, `FRONTEND_URL`)
3. Set build command: `npm run build && npx prisma generate`
4. Set start command: `npm run start`
