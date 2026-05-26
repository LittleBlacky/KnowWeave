export const appEnv = process.env.NEXT_PUBLIC_APP_ENV ?? "development";

export const apiBaseUrl = (
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1"
).replace(/\/+$/, "");

export const enableMocks = process.env.NEXT_PUBLIC_ENABLE_MOCKS === "true";
