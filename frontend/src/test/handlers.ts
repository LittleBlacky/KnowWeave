import { http, HttpResponse } from "msw";

export const handlers = [
  http.get("http://localhost/api/v1/health", () =>
    HttpResponse.json({
      status: "ok",
      service: "knowweave-frontend-msw",
      version: "0.1.0",
    }),
  ),
];
