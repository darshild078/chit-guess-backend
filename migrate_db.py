import asyncio
from sqlalchemy import text
from app.database import engine

async def migrate():
    async with engine.begin() as conn:
        print("Migrating database schema for 3 Game Modes & Scoring Features...")

        # 1. Add totalRounds, timerSeconds, gameMode, promptCategory, customPrompt to Room
        await conn.execute(text("""
            ALTER TABLE "Room" 
            ADD COLUMN IF NOT EXISTS "totalRounds" INTEGER NOT NULL DEFAULT 3;
        """))
        await conn.execute(text("""
            ALTER TABLE "Room" 
            ADD COLUMN IF NOT EXISTS "timerSeconds" INTEGER NOT NULL DEFAULT 60;
        """))
        await conn.execute(text("""
            ALTER TABLE "Room" 
            ADD COLUMN IF NOT EXISTS "gameMode" VARCHAR NOT NULL DEFAULT 'confessions';
        """))
        await conn.execute(text("""
            ALTER TABLE "Room" 
            ADD COLUMN IF NOT EXISTS "promptCategory" VARCHAR NOT NULL DEFAULT 'general';
        """))
        await conn.execute(text("""
            ALTER TABLE "Room" 
            ADD COLUMN IF NOT EXISTS "customPrompt" VARCHAR;
        """))

        # 2. Add score to Participant
        await conn.execute(text("""
            ALTER TABLE "Participant" 
            ADD COLUMN IF NOT EXISTS "score" INTEGER NOT NULL DEFAULT 0;
        """))

        # 3. Add mode-specific fields to GameRound
        await conn.execute(text("""
            ALTER TABLE "GameRound" 
            ADD COLUMN IF NOT EXISTS "prompt" VARCHAR;
        """))
        await conn.execute(text("""
            ALTER TABLE "GameRound" 
            ADD COLUMN IF NOT EXISTS "secretTopic" VARCHAR;
        """))
        await conn.execute(text("""
            ALTER TABLE "GameRound" 
            ADD COLUMN IF NOT EXISTS "secretWord" VARCHAR;
        """))
        await conn.execute(text("""
            ALTER TABLE "GameRound" 
            ADD COLUMN IF NOT EXISTS "chameleonParticipantId" VARCHAR;
        """))
        await conn.execute(text("""
            ALTER TABLE "GameRound" 
            ADD COLUMN IF NOT EXISTS "wordChoices" VARCHAR;
        """))
        await conn.execute(text("""
            ALTER TABLE "GameRound" 
            ADD COLUMN IF NOT EXISTS "chameleonEscaped" BOOLEAN DEFAULT FALSE;
        """))
        await conn.execute(text("""
            ALTER TABLE "GameRound" 
            ADD COLUMN IF NOT EXISTS "chameleonGuessedWord" BOOLEAN DEFAULT FALSE;
        """))

        # 4. Create or update RoundGuess table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS "RoundGuess" (
                "id" VARCHAR PRIMARY KEY,
                "roomId" VARCHAR NOT NULL REFERENCES "Room"("id") ON DELETE CASCADE,
                "roundId" VARCHAR NOT NULL REFERENCES "GameRound"("id") ON DELETE CASCADE,
                "guesserId" VARCHAR NOT NULL REFERENCES "Participant"("id") ON DELETE CASCADE,
                "chitId" VARCHAR,
                "guessedSenderId" VARCHAR NOT NULL REFERENCES "Participant"("id") ON DELETE CASCADE,
                "isCorrect" BOOLEAN NOT NULL DEFAULT FALSE,
                "isDoubleDown" BOOLEAN NOT NULL DEFAULT FALSE,
                "createdAt" TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
        """))
        await conn.execute(text("""
            ALTER TABLE "RoundGuess" 
            ADD COLUMN IF NOT EXISTS "isDoubleDown" BOOLEAN NOT NULL DEFAULT FALSE;
        """))

        print("Database schema migration complete!")

if __name__ == "__main__":
    asyncio.run(migrate())
