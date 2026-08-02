export const RoomStatus = {
  lobby: 'lobby',
  waiting: 'waiting',
  submissions_open: 'submissions_open',
  submissions_closed: 'submissions_closed',
  guessing: 'guessing',
  revealed: 'revealed',
  completed: 'completed',
  ended: 'ended',
} as const;

export type RoomStatus = (typeof RoomStatus)[keyof typeof RoomStatus];

export const RoundStatus = {
  waiting: 'waiting',
  submissions_open: 'submissions_open',
  submissions_closed: 'submissions_closed',
  guessing: 'guessing',
  revealed: 'revealed',
  completed: 'completed',
} as const;

export type RoundStatus = (typeof RoundStatus)[keyof typeof RoundStatus];

export const ParticipantRole = {
  owner: 'owner',
  player: 'player',
} as const;

export type ParticipantRole = (typeof ParticipantRole)[keyof typeof ParticipantRole];
