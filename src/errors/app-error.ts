export class AppError extends Error {
  public statusCode: number;
  public code: string;
  public fieldErrors?: Record<string, string[]>;

  constructor(statusCode: number, code: string, message: string, fieldErrors?: Record<string, string[]>) {
    super(message);
    this.statusCode = statusCode;
    this.code = code;
    this.fieldErrors = fieldErrors;
    Error.captureStackTrace(this, this.constructor);
  }

  static badRequest(code: string, message: string, fieldErrors?: Record<string, string[]>) {
    return new AppError(400, code, message, fieldErrors);
  }

  static unauthorized(code: string, message: string) {
    return new AppError(401, code, message);
  }

  static forbidden(code: string, message: string) {
    return new AppError(403, code, message);
  }

  static notFound(code: string, message: string) {
    return new AppError(404, code, message);
  }

  static conflict(code: string, message: string) {
    return new AppError(409, code, message);
  }

  static tooManyRequests(code: string, message: string) {
    return new AppError(429, code, message);
  }

  static internalError(code: string, message: string) {
    return new AppError(500, code, message);
  }
}
