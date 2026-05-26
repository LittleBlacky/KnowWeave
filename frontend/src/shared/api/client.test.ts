import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";

import { server } from "@/test/server";

import { ApiClient } from "./client";

describe("ApiClient", () => {
  it("normalizes base URLs and resource paths", () => {
    const client = new ApiClient("http://localhost:8000/api/v1/");

    expect(client.baseUrl).toBe("http://localhost:8000/api/v1");
    expect(client.url("files")).toBe("http://localhost:8000/api/v1/files");
    expect(client.url("/chunks")).toBe("http://localhost:8000/api/v1/chunks");
  });

  it("unwraps standard response envelopes", async () => {
    server.use(
      http.get("http://localhost:8000/api/v1/files", () =>
        HttpResponse.json({
          data: [{ id: "file_001", name: "policy.md" }],
          error: null,
          request_id: "req_files",
        }),
      ),
    );
    const client = new ApiClient("http://localhost:8000/api/v1");

    await expect(client.get("/files")).resolves.toEqual([{ id: "file_001", name: "policy.md" }]);
  });

  it("maps error envelopes to ApiError", async () => {
    server.use(
      http.get("http://localhost:8000/api/v1/files/missing", () =>
        HttpResponse.json(
          {
            data: null,
            error: {
              code: "FILE_NOT_FOUND",
              message: "File not found.",
              details: { file_id: "missing" },
            },
            request_id: "req_missing",
          },
          { status: 404 },
        ),
      ),
    );
    const client = new ApiClient("http://localhost:8000/api/v1");

    await expect(client.get("/files/missing")).rejects.toMatchObject({
      code: "FILE_NOT_FOUND",
      details: { file_id: "missing" },
      message: "File not found.",
      requestId: "req_missing",
      status: 404,
    });
  });
});
