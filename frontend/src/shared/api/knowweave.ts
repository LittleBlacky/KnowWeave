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
