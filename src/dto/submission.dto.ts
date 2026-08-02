export interface MySubmissionDTO {
  body: string;
  submittedAt: Date;
  updatedAt: Date;
}

export interface SubmissionStatusDTO {
  hasSubmitted: boolean;
  canEdit: boolean;
  canDelete: boolean;
  canSubmit: boolean;
}
