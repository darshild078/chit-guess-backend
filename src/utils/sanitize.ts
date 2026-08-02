export function trimAndClean(str: string): string {
  if (!str) return '';
  return str.trim().replace(/[\u0000-\u001F\u007F-\u009F]/g, '');
}

export function isBlankOrEmpty(str: string): boolean {
  return !str || str.trim().length === 0;
}
