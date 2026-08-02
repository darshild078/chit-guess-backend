import crypto from 'crypto';

const ALLOWED_CHARS = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';

export function generateRoomCode(): string {
  let code = '';
  const bytes = crypto.randomBytes(6);
  for (let i = 0; i < 6; i++) {
    code += ALLOWED_CHARS[bytes[i]! % ALLOWED_CHARS.length];
  }
  return code;
}
