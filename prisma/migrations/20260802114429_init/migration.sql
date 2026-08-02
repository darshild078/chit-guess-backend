-- CreateEnum
CREATE TYPE "RoomStatus" AS ENUM ('lobby', 'waiting', 'submissions_open', 'submissions_closed', 'guessing', 'revealed', 'completed', 'ended');

-- CreateEnum
CREATE TYPE "RoundStatus" AS ENUM ('waiting', 'submissions_open', 'submissions_closed', 'guessing', 'revealed', 'completed');

-- CreateEnum
CREATE TYPE "ParticipantRole" AS ENUM ('owner', 'player');

-- CreateTable
CREATE TABLE "Room" (
    "id" TEXT NOT NULL,
    "code" TEXT NOT NULL,
    "title" TEXT,
    "status" "RoomStatus" NOT NULL DEFAULT 'lobby',
    "ownerParticipantId" TEXT,
    "maxPlayers" INTEGER NOT NULL DEFAULT 10,
    "locked" BOOLEAN NOT NULL DEFAULT false,
    "currentRoundNumber" INTEGER NOT NULL DEFAULT 0,
    "expiresAt" TIMESTAMP(3) NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "Room_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Participant" (
    "id" TEXT NOT NULL,
    "roomId" TEXT NOT NULL,
    "displayName" TEXT NOT NULL,
    "role" "ParticipantRole" NOT NULL,
    "connected" BOOLEAN NOT NULL DEFAULT false,
    "removed" BOOLEAN NOT NULL DEFAULT false,
    "sessionVersion" INTEGER NOT NULL DEFAULT 1,
    "joinedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "lastSeenAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "Participant_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "GameRound" (
    "id" TEXT NOT NULL,
    "roomId" TEXT NOT NULL,
    "roundNumber" INTEGER NOT NULL,
    "status" "RoundStatus" NOT NULL DEFAULT 'waiting',
    "aliasEpoch" INTEGER NOT NULL DEFAULT 0,
    "identitiesRevealed" BOOLEAN NOT NULL DEFAULT false,
    "submissionsOpenedAt" TIMESTAMP(3),
    "submissionsClosedAt" TIMESTAMP(3),
    "revealedAt" TIMESTAMP(3),
    "completedAt" TIMESTAMP(3),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "GameRound_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ChitMessage" (
    "id" TEXT NOT NULL,
    "roomId" TEXT NOT NULL,
    "roundId" TEXT NOT NULL,
    "senderId" TEXT NOT NULL,
    "body" TEXT NOT NULL,
    "isRead" BOOLEAN NOT NULL DEFAULT false,
    "isGuessed" BOOLEAN NOT NULL DEFAULT false,
    "guessedParticipantId" TEXT,
    "submittedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "ChitMessage_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "RoundAlias" (
    "id" TEXT NOT NULL,
    "roundId" TEXT NOT NULL,
    "aliasEpoch" INTEGER NOT NULL,
    "participantId" TEXT NOT NULL,
    "aliasNumber" INTEGER NOT NULL,
    "opaqueAliasId" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "RoundAlias_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "Room_code_key" ON "Room"("code");

-- CreateIndex
CREATE INDEX "Participant_roomId_idx" ON "Participant"("roomId");

-- CreateIndex
CREATE UNIQUE INDEX "Participant_roomId_displayName_key" ON "Participant"("roomId", "displayName");

-- CreateIndex
CREATE INDEX "GameRound_roomId_idx" ON "GameRound"("roomId");

-- CreateIndex
CREATE UNIQUE INDEX "GameRound_roomId_roundNumber_key" ON "GameRound"("roomId", "roundNumber");

-- CreateIndex
CREATE INDEX "ChitMessage_roomId_roundId_idx" ON "ChitMessage"("roomId", "roundId");

-- CreateIndex
CREATE UNIQUE INDEX "ChitMessage_roundId_senderId_key" ON "ChitMessage"("roundId", "senderId");

-- CreateIndex
CREATE UNIQUE INDEX "RoundAlias_opaqueAliasId_key" ON "RoundAlias"("opaqueAliasId");

-- CreateIndex
CREATE INDEX "RoundAlias_roundId_aliasEpoch_idx" ON "RoundAlias"("roundId", "aliasEpoch");

-- CreateIndex
CREATE UNIQUE INDEX "RoundAlias_roundId_aliasEpoch_participantId_key" ON "RoundAlias"("roundId", "aliasEpoch", "participantId");

-- CreateIndex
CREATE UNIQUE INDEX "RoundAlias_roundId_aliasEpoch_aliasNumber_key" ON "RoundAlias"("roundId", "aliasEpoch", "aliasNumber");

-- AddForeignKey
ALTER TABLE "Participant" ADD CONSTRAINT "Participant_roomId_fkey" FOREIGN KEY ("roomId") REFERENCES "Room"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "GameRound" ADD CONSTRAINT "GameRound_roomId_fkey" FOREIGN KEY ("roomId") REFERENCES "Room"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ChitMessage" ADD CONSTRAINT "ChitMessage_roundId_fkey" FOREIGN KEY ("roundId") REFERENCES "GameRound"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ChitMessage" ADD CONSTRAINT "ChitMessage_senderId_fkey" FOREIGN KEY ("senderId") REFERENCES "Participant"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "RoundAlias" ADD CONSTRAINT "RoundAlias_roundId_fkey" FOREIGN KEY ("roundId") REFERENCES "GameRound"("id") ON DELETE CASCADE ON UPDATE CASCADE;
