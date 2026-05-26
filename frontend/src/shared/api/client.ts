import { apiBaseUrl } from "@/shared/config/env";

import { ApiError, type ApiErrorPayload } from "./errors";

type ApiEnvelope<TData> = {
  data: TData | null;
  error: ApiErrorPayload | null;
  request_id: string | null;
};

type RequestOptions = {
  body?: BodyInit | Record<string, unknown>;
  headers?: HeadersInit;
  method?: "DELETE" | "GET" | "PATCH" | "POST" | "PUT";
  signal?: AbortSignal;
};

export class ApiClient {
  readonly baseUrl: string;

  constructor(baseUrl = apiBaseUrl) {
    this.baseUrl = baseUrl.replace(/\/+$/, "");
  }

  get<TData>(path: string, options: Omit<RequestOptions, "body" | "method"> = {}) {
    return this.request<TData>(path, { ...options, method: "GET" });
  }

  post<TData>(path: string, body?: RequestOptions["body"], options: RequestOptions = {}) {
    return this.request<TData>(path, { ...options, body, method: "POST" });
  }

  patch<TData>(path: string, body?: RequestOptions["body"], options: RequestOptions = {}) {
    return this.request<TData>(path, { ...options, body, method: "PATCH" });
  }

  delete<TData>(path: string, options: Omit<RequestOptions, "body" | "method"> = {}) {
    return this.request<TData>(path, { ...options, method: "DELETE" });
  }

  async request<TData>(path: string, options: RequestOptions = {}): Promise<TData> {
    const response = await fetch(this.url(path), this.toFetchInit(options));
    const envelope = (await response.json()) as ApiEnvelope<TData>;

    if (!response.ok || envelope.error) {
      throw new ApiError({
        error: envelope.error ?? {
          code: "HTTP_ERROR",
          message: response.statusText || "Request failed.",
        },
        requestId: envelope.request_id ?? response.headers.get("x-request-id"),
        status: response.status,
      });
    }

    return envelope.data as TData;
  }

  url(path: string): string {
    const normalizedPath = path.startsWith("/") ? path : `/${path}`;
    return `${this.baseUrl}${normalizedPath}`;
  }

  private toFetchInit({ body, headers, method = "GET", signal }: RequestOptions): RequestInit {
    const nextHeaders = new Headers(headers);
    const init: RequestInit = { headers: nextHeaders, method, signal };

    if (body instanceof FormData) {
      init.body = body;
      return init;
    }

    if (body !== undefined) {
      nextHeaders.set("content-type", "application/json");
      init.body = typeof body === "string" ? body : JSON.stringify(body);
    }

    return init;
  }
}

export const apiClient = new ApiClient();
