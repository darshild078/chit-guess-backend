export interface AnonymousChitDTO {
  anonymousChitId: string;
  alias: string;
  body: string;
  submittedAt: Date;
  isRead: boolean;
  isGuessed: boolean;
}

export interface AnonymousInboxDTO {
  roundNumber: number;
  aliasEpoch: number;
  chits: AnonymousChitDTO[];
}
