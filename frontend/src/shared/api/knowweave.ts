import { apiClient } from "./client";

export type KnowledgeFile = {
  id: string;
  name: string;
  original_filename: string;
  file_type: string;
  mime_type: string;
  size_bytes: number;
  sha256: string;
  directory_path: string;
  status: string;
};

export type FileListResponse = {
  items: KnowledgeFile[];
  total: number;
};

export type ParseResult = {
  id: string;
  file_id: string;
  parser_name: string;
  parser_version: string;
  status: string;
  warnings: Array<{ code: string; message: string }>;
  block_count: number;
};

export type SourceSpan = {
  id: string;
  document_block_id: string | null;
  page_number: number | null;
  char_start: number | null;
  char_end: number | null;
  line_start: number | null;
  line_end: number | null;
  preview_text: string;
};

export type Chunk = {
  id: string;
  file_id: string;
  parse_result_id: string;
  document_block_id: string | null;
  chunk_index: number;
  chunk_type: string;
  raw_content: string;
  edited_content: string | null;
  is_manually_edited: boolean;
  status: string;
  summary: string | null;
  quality_signals: Array<Record<string, unknown>>;
  char_count: number;
  search_text: string;
  is_searchable: boolean;
  source_spans: SourceSpan[];
};

export type ChunkListResponse = {
  items: Chunk[];
  total: number;
};

export type SearchResult = {
  result_id: string;
  result_type: string;
  title: string;
  preview_text: string;
  score: string;
  rank: number;
  source: {
    file_id: string | null;
    file_name: string | null;
    source_span_id: string | null;
    page_number: number | null;
    line_start: number | null;
    line_end: number | null;
    source_available: boolean;
  };
  status: Record<string, unknown>;
  metadata: Record<string, unknown>;
};

export type SearchResponse = {
  retrieval_run_id: string;
  query: string;
  strategy: string;
  results: SearchResult[];
};

export type Tag = {
  id: string;
  name: string;
  description: string | null;
  color: string | null;
  binding_count?: number;
  created_at: string;
  updated_at: string;
};

export type TagListResponse = {
  items: Tag[];
  total: number;
};

export type KnowledgeUnitSource = {
  id: string;
  knowledge_unit_id: string;
  file_id: string | null;
  chunk_id: string | null;
  source_span_id: string | null;
  source_type: string;
  source_label: string;
  source_available: boolean;
  created_at: string;
};

export type KnowledgeUnit = {
  id: string;
  title: string;
  unit_type: string;
  content: string;
  summary: string | null;
  status: string;
  trust_level: number | null;
  applicable_scope: string | null;
  created_from: string;
  search_text: string;
  metadata_: Record<string, unknown>;
  source_count: number;
  tags: Tag[];
  created_at: string;
  updated_at: string;
  verified_at: string | null;
  archived_at: string | null;
};

export type KnowledgeUnitDetail = KnowledgeUnit & {
  sources: KnowledgeUnitSource[];
};

export type KnowledgeUnitListResponse = {
  items: KnowledgeUnit[];
  total: number;
};

export type Wiki = {
  id: string;
  title: string;
  wiki_type: string;
  status: string;
  summary: string | null;
  content_markdown: string;
  source_file_id: string | null;
  generation_prompt_version: string | null;
  search_text: string;
  metadata_: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  verified_at: string | null;
};

export type WikiListResponse = {
  items: Wiki[];
  total: number;
};

export type Citation = {
  id: string;
  target_type: string;
  target_id: string;
  file_id: string | null;
  chunk_id: string | null;
  source_span_id: string | null;
  label: string | null;
  preview_text: string;
  source_available: boolean;
};

export type CitationListResponse = {
  items: Citation[];
  total: number;
};

export function listFiles() {
  return apiClient.get<FileListResponse>("/files");
}

export function uploadFile(file: File) {
  const form = new FormData();
  form.append("file", file, file.name);
  return apiClient.post<KnowledgeFile>("/files/upload", form);
}

export function parseFile(fileId: string) {
  return apiClient.post<ParseResult>(`/files/${fileId}/parse`);
}

export function buildFileChunks(fileId: string) {
  return apiClient.post<ChunkListResponse>(`/files/${fileId}/chunks/build`);
}

export function listFileChunks(fileId: string) {
  return apiClient.get<ChunkListResponse>(`/files/${fileId}/chunks`);
}

export function updateChunk(chunkId: string, editedContent: string) {
  return apiClient.patch<Chunk>(`/chunks/${chunkId}`, { edited_content: editedContent });
}

export function ignoreChunk(chunkId: string) {
  return apiClient.post<Chunk>(`/chunks/${chunkId}/ignore`);
}

export function verifyChunk(chunkId: string) {
  return apiClient.post<Chunk>(`/chunks/${chunkId}/verify`);
}

export function searchKnowledge(query: string, topK = 10) {
  return apiClient.post<SearchResponse>("/search", { query, top_k: topK });
}

export function listTags() {
  return apiClient.get<TagListResponse>("/tags");
}

export function createTag(input: { name: string; description?: string; color?: string }) {
  return apiClient.post<Tag>("/tags", input);
}

export function bindTag(input: { tag_id: string; target_type: string; target_id: string }) {
  return apiClient.post<{ id: string; tag_id: string; target_type: string; target_id: string }>(
    "/tag-bindings",
    input,
  );
}

export function listKnowledgeUnits(params: {
  status?: string;
  tag?: string;
  source_file_id?: string;
  unit_type?: string;
} = {}) {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value) {
      query.set(key, value);
    }
  }
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return apiClient.get<KnowledgeUnitListResponse>(`/knowledge-units${suffix}`);
}

export function getKnowledgeUnit(knowledgeUnitId: string) {
  return apiClient.get<KnowledgeUnitDetail>(`/knowledge-units/${knowledgeUnitId}`);
}

export function updateKnowledgeUnit(
  knowledgeUnitId: string,
  input: {
    title: string;
    content: string;
    unit_type?: string;
    summary?: string | null;
    status?: string;
    applicable_scope?: string | null;
    tag_ids?: string[];
    source_chunk_ids?: string[];
  },
) {
  return apiClient.patch<KnowledgeUnit>(`/knowledge-units/${knowledgeUnitId}`, {
    ...input,
    unit_type: input.unit_type ?? "concept",
    status: input.status ?? "draft",
    tag_ids: input.tag_ids ?? [],
    source_chunk_ids: input.source_chunk_ids ?? [],
  });
}

export function listWikiPages() {
  return apiClient.get<WikiListResponse>("/wiki");
}

export function getWiki(wikiId: string) {
  return apiClient.get<Wiki>(`/wiki/${wikiId}`);
}

export function listWikiCitations(wikiId: string) {
  return apiClient.get<CitationListResponse>(`/wiki/${wikiId}/citations`);
}

export function updateWiki(
  wikiId: string,
  input: {
    content_markdown: string;
    change_summary: string;
    status?: string;
    title?: string;
    summary?: string | null;
  },
) {
  return apiClient.patch<Wiki>(`/wiki/${wikiId}`, input);
}
