export type ApiErrorPayload = {
  code: string;
  message: string;
  details?: Record<string, unknown>;
};

export class ApiError extends Error {
  readonly code: string;
  readonly details: Record<string, unknown>;
  readonly requestId: string | null;
  readonly status: number;

  constructor({
    error,
    requestId,
    status,
  }: {
    error: ApiErrorPayload;
    requestId: string | null;
    status: number;
  }) {
    super(error.message);
    this.name = "ApiError";
    this.code = error.code;
    this.details = error.details ?? {};
    this.requestId = requestId;
    this.status = status;
  }
}
