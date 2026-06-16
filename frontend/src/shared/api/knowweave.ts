import {apiClient} from "./client";

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
  warnings: Array<{code: string; message: string}>;
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

export type DocumentBlock = {
  id: string;
  file_id: string;
  parse_result_id: string;
  block_index: number;
  block_type: string;
  raw_content: string;
  normalized_content: string | null;
  is_ignored: boolean;
  page_number: number | null;
  line_start: number | null;
  line_end: number | null;
  char_start: number | null;
  char_end: number | null;
  metadata: Record<string, unknown>;
  created_at: string;
};

export type DocumentBlockListResponse = {
  items: DocumentBlock[];
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

export type ExtractionResponse = {
  extracted: number;
  skipped_duplicates: number;
  units: KnowledgeUnit[];
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

export type Feedback = {
  id: string;
  target_type: string;
  target_id: string;
  feedback_type: string;
  comment: string | null;
  status: string;
  metadata_: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type EvaluationSample = {
  id: string;
  question: string;
  expected_answer: string | null;
  expected_source_files: string[];
  expected_source_chunks: string[];
  created_from: string;
  source_chat_message_id: string | null;
  source_feedback_id: string | null;
  status: string;
  difficulty: string | null;
  metadata_: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type EvaluationSampleListResponse = {
  items: EvaluationSample[];
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

export function getFileDetail(fileId: string) {
  return apiClient.get<KnowledgeFile>(`/files/${fileId}`);
}

export function generateFileWiki(fileId: string) {
  return apiClient.post<Wiki>(`/files/${fileId}/wiki`);
}

export function listDocumentBlocks(fileId: string) {
  return apiClient.get<DocumentBlockListResponse>(
    `/files/${fileId}/document-blocks`,
  );
}

export function autoGenerateKnowledgeUnits(fileId: string, batchSize = 6) {
  return apiClient.post<ExtractionResponse>(
    `/knowledge-units/files/${fileId}/generate?batch_size=${batchSize}`,
  );
}

export function batchUpdateKnowledgeUnitStatus(
  unitIds: string[],
  status: string,
) {
  return apiClient.post<{updated: number; status: string}>(
    "/knowledge-units/batch-update-status",
    {unit_ids: unitIds, status},
  );
}

export function listFileChunks(fileId: string) {
  return apiClient.get<ChunkListResponse>(`/files/${fileId}/chunks`);
}

export function updateChunk(chunkId: string, editedContent: string) {
  return apiClient.patch<Chunk>(`/chunks/${chunkId}`, {
    edited_content: editedContent,
  });
}

export function ignoreChunk(chunkId: string) {
  return apiClient.post<Chunk>(`/chunks/${chunkId}/ignore`);
}

export function verifyChunk(chunkId: string) {
  return apiClient.post<Chunk>(`/chunks/${chunkId}/verify`);
}

export function searchKnowledge(
  query: string,
  topK = 10,
  targetTypes: string[] = ["chunk"],
) {
  return apiClient.post<SearchResponse>("/search", {
    query,
    target_types: targetTypes,
    top_k: topK,
  });
}

export function listTags() {
  return apiClient.get<TagListResponse>("/tags");
}

export function createTag(input: {
  name: string;
  description?: string;
  color?: string;
}) {
  return apiClient.post<Tag>("/tags", input);
}

export function bindTag(input: {
  tag_id: string;
  target_type: string;
  target_id: string;
}) {
  return apiClient.post<{
    id: string;
    tag_id: string;
    target_type: string;
    target_id: string;
  }>("/tag-bindings", input);
}

export function listKnowledgeUnits(
  params: {
    status?: string;
    tag?: string;
    source_file_id?: string;
    unit_type?: string;
  } = {},
) {
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
  return apiClient.get<KnowledgeUnitDetail>(
    `/knowledge-units/${knowledgeUnitId}`,
  );
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

export function createFeedback(input: {
  target_type: string;
  target_id: string;
  feedback_type: string;
  comment?: string;
  metadata?: Record<string, unknown>;
}) {
  return apiClient.post<Feedback>("/feedback", input);
}

export function createEvaluationSampleFromFeedback(feedbackId: string) {
  return apiClient.post<EvaluationSample>(
    `/feedback/${feedbackId}/to-evaluation-sample`,
  );
}

export function listEvaluationSamples(status?: string) {
  const suffix = status ? `?status=${encodeURIComponent(status)}` : "";
  return apiClient.get<EvaluationSampleListResponse>(
    `/evaluation-samples${suffix}`,
  );
}

export function getEvaluationSample(sampleId: string) {
  return apiClient.get<EvaluationSample>(`/evaluation-samples/${sampleId}`);
}

export function updateEvaluationSample(
  sampleId: string,
  input: {
    question?: string;
    expected_answer?: string | null;
    status?: string;
    difficulty?: string | null;
  },
) {
  return apiClient.patch<EvaluationSample>(
    `/evaluation-samples/${sampleId}`,
    input,
  );
}

export type EvaluationMetrics = {
  total_samples: number;
  verified: number;
  candidates: number;
  with_answer: number;
  with_sources: number;
  source_traceability_pct: number;
  answer_coverage_pct: number;
  message?: string;
};

export function getEvaluationMetrics() {
  return apiClient.get<EvaluationMetrics>("/evaluation/metrics");
}

export function createEvaluationSampleFromChatMessage(messageId: string) {
  return apiClient.post<EvaluationSample>(
    `/chat/messages/${messageId}/to-evaluation-sample`,
  );
}

// ---- Curation ----

export type CurationReport = {
  generated_at: string;
  total_chunks: number;
  total_knowledge_units: number;
  total_wiki_pages: number;
  total_feedback_count: number;
  high_value_chunks: Array<{
    chunk_id: string;
    file_name: string;
    preview: string;
    status: string;
    char_count: number;
  }>;
  suggested_topics: string[];
  frequent_questions: string[];
  stale_items: Array<{
    id: string;
    type: string;
    preview: string;
    last_updated: string;
  }>;
  summary: string;
};

export function getCurationReport() {
  return apiClient.get<CurationReport>("/curation/report");
}

// ---- System Config ----

export type SystemConfig = {
  app_name: string;
  version: string;
  environment: string;
  provider: {
    type: string;
    qwen_enabled: boolean;
    base_url: string;
    timeout_seconds: number;
  };
  models: {
    chat: string;
    generation: string;
    embedding: string;
    rerank: string;
  };
};

export function getSystemConfig() {
  return apiClient.get<SystemConfig>("/system/config");
}

export type UpdateConfigInput = {
  qwen_api_key?: string;
  qwen_chat_model?: string;
  qwen_generation_model?: string;
  qwen_embedding_model?: string;
  qwen_rerank_model?: string;
  qwen_base_url?: string;
};

export type UpdateConfigResponse = {
  updated: string[];
  changed: Record<string, string | number>;
  config: SystemConfig;
};

export function updateSystemConfig(input: UpdateConfigInput) {
  return apiClient.patch<UpdateConfigResponse>("/system/config", input);
}

// ---- Wiki ----

export type WikiRevision = {
  id: string;
  wiki_page_id: string;
  revision_number: number;
  title: string;
  content_markdown: string;
  summary: string | null;
  status: string;
  change_summary: string;
  edit_source: string;
  created_at: string;
};

export function listWikiRevisions(wikiId: string) {
  return apiClient.get<WikiRevision[]>(`/wiki/${wikiId}/revisions`);
}

export function rollbackWiki(wikiId: string, revisionId: string) {
  return apiClient.post<Wiki>(
    `/wiki/${wikiId}/revisions/${revisionId}/rollback`,
  );
}

export function createTopicWiki(input: {
  theme: string;
  file_ids?: string[];
  knowledge_unit_ids?: string[];
}) {
  return apiClient.post<Wiki>("/wiki/topic", input);
}

export function createFaqWiki(fileId: string) {
  return apiClient.post<Wiki>(`/files/${fileId}/faq-wiki`);
}

// ---- Agent ----

export function generateExpertAgent(name: string, fileIds?: string[]) {
  const params = new URLSearchParams({name});
  if (fileIds?.length) {
    fileIds.forEach((id) => params.append("file_ids", id));
  }
  return apiClient.post<{
    session_id: string;
    title: string;
    knowledge_summary: Record<string, number>;
    system_prompt_preview: string;
  }>(`/agent/generate?${params.toString()}`);
}

// ---- Chat Sessions ----

export type ChatSession = {
  id: string;
  title: string;
  scope: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type ChatSessionDetail = ChatSession & {
  messages: Array<{
    id: string;
    session_id: string;
    role: string;
    content_markdown: string;
    status: string;
    model_provider: string | null;
    model_name: string | null;
    prompt_version: string | null;
    created_at: string;
  }>;
};

export type ChatSessionListResponse = {
  items: ChatSession[];
  total: number;
};

export function listChatSessions() {
  return apiClient.get<ChatSessionListResponse>("/chat/sessions");
}

export function createChatSession(title: string) {
  return apiClient.post<ChatSession>("/chat/sessions", {title});
}

export function getChatSession(sessionId: string) {
  return apiClient.get<ChatSessionDetail>(`/chat/sessions/${sessionId}`);
}

export function deleteChatSession(sessionId: string) {
  return apiClient.delete<void>(`/chat/sessions/${sessionId}`);
}

