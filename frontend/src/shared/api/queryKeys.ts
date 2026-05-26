export const queryKeys = {
  dashboard: {
    summary: ["dashboard", "summary"] as const,
  },
  files: {
    list: (filters?: unknown) => ["files", "list", filters ?? {}] as const,
    detail: (fileId: string) => ["files", "detail", fileId] as const,
    blocks: (fileId: string) => ["files", "blocks", fileId] as const,
    chunks: (fileId: string, filters?: unknown) =>
      ["files", "chunks", fileId, filters ?? {}] as const,
  },
  chunks: {
    list: (filters?: unknown) => ["chunks", "list", filters ?? {}] as const,
    detail: (chunkId: string) => ["chunks", "detail", chunkId] as const,
  },
  search: {
    run: (retrievalRunId: string) => ["search", "run", retrievalRunId] as const,
  },
  wiki: {
    list: (filters?: unknown) => ["wiki", "list", filters ?? {}] as const,
    detail: (wikiPageId: string) => ["wiki", "detail", wikiPageId] as const,
  },
  chat: {
    sessions: () => ["chat", "sessions"] as const,
    session: (sessionId: string) => ["chat", "session", sessionId] as const,
  },
  evaluation: {
    samples: (filters?: unknown) => ["evaluation", "samples", filters ?? {}] as const,
  },
};
