import asyncio
from sqlalchemy import text
from app.database import engine

async def migrate():
    async with engine.begin() as conn:
        print("Migrating database schema...")

        # 1. Add totalRounds and timerSeconds to Room if not exist
        await conn.execute(text("""
            ALTER TABLE "Room" 
            ADD COLUMN IF NOT EXISTS "totalRounds" INTEGER NOT NULL DEFAULT 3;
        """))
        await conn.execute(text("""
            ALTER TABLE "Room" 
            ADD COLUMN IF NOT EXISTS "timerSeconds" INTEGER NOT NULL DEFAULT 60;
        """))

        # 2. Add score to Participant if not exist
        await conn.execute(text("""
            ALTER TABLE "Participant" 
            ADD COLUMN IF NOT EXISTS "score" INTEGER NOT NULL DEFAULT 0;
        """))

        # 3. Create RoundGuess table if not exist
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS "RoundGuess" (
                "id" VARCHAR PRIMARY KEY,
                "roomId" VARCHAR NOT NULL REFERENCES "Room"("id") ON DELETE CASCADE,
                "roundId" VARCHAR NOT NULL REFERENCES "GameRound"("id") ON DELETE CASCADE,
                "guesserId" VARCHAR NOT NULL REFERENCES "Participant"("id") ON DELETE CASCADE,
                "chitId" VARCHAR NOT NULL REFERENCES "ChitMessage"("id") ON DELETE CASCADE,
                "guessedSenderId" VARCHAR NOT NULL REFERENCES "Participant"("id") ON DELETE CASCADE,
                "isCorrect" BOOLEAN NOT NULL DEFAULT FALSE,
                "createdAt" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                CONSTRAINT "RoundGuess_roundId_guesserId_chitId_key" UNIQUE ("roundId", "guesserId", "chitId")
            );
        """))

        print("Database schema migration complete!")

if __name__ == "__main__":
    asyncio.run(migrate())
