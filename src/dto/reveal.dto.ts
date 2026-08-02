export interface RevealedChitDTO {
  chitId: string;
  senderDisplayName: string;
  body: string;
  submittedAt: Date;
  guessedDisplayName?: string;
  wasCorrect?: boolean;
}

export interface RevealResultsDTO {
  roundNumber: number;
  chits: RevealedChitDTO[];
}
