import { Request, Response } from 'express';

export const healthController = {
  check(req: Request, res: Response) {
    res.json({ status: 'ok' });
  }
};
