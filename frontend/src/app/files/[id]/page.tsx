"use client";

import {
  BookOpenCheck,
  Boxes,
  FileText,
  Loader2,
  Play,
  ChevronLeft,
} from "lucide-react";
import Link from "next/link";
import {useParams} from "next/navigation";
import {useEffect, useState} from "react";

import {AppShell} from "@/app-shell/AppShell";
import {
  listDocumentBlocks,
  listFileChunks,
  getFileDetail,
  generateFileWiki,
  parseFile,
  buildFileChunks,
  type KnowledgeFile,
  type DocumentBlock,
  type Chunk,
} from "@/shared/api/knowweave";

export default function FileDetailPage() {
  const params = useParams();
  const fileId = params.id as string;

  const [file, setFile] = useState<KnowledgeFile | null>(null);
  const [blocks, setBlocks] = useState<DocumentBlock[]>([]);
  const [chunks, setChunks] = useState<Chunk[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionStatus, setActionStatus] = useState("");

  useEffect(() => {
    async function fetch() {
      try {
        const [fileRes, blockRes, chunkRes] = await Promise.all([
          getFileDetail(fileId),
          listDocumentBlocks(fileId),
          listFileChunks(fileId),
        ]);
        setFile(fileRes);
        setBlocks(blockRes.items);
        setChunks(chunkRes.items);
      } catch {
        // keep empty state
      } finally {
        setLoading(false);
      }
    }
    void fetch();
  }, [fileId]);

  async function handleParse() {
    setActionStatus("Parsing…");
    const result = await parseFile(fileId);
    setFile((prev) => (prev ? {...prev, status: result.status} : prev));
    const blockRes = await listDocumentBlocks(fileId);
    setBlocks(blockRes.items);
    setActionStatus(result.status);
  }

  async function handleBuildChunks() {
    setActionStatus("Building chunks…");
    const result = await buildFileChunks(fileId);
    setChunks(result.items);
    setActionStatus(`${result.total} chunks built`);
  }

  async function handleGenerateWiki() {
    setActionStatus("Generating Wiki…");
    try {
      const wiki = await generateFileWiki(fileId);
      setActionStatus(`Wiki "${wiki.title}" created`);
    } catch {
      setActionStatus("Wiki generation failed");
    }
  }

  if (loading) {
    return (
      <AppShell>
        <div className="flex items-center justify-center py-20">
          <Loader2
            aria-hidden="true"
            className="animate-spin text-[#275a53]"
            size={32}
          />
        </div>
      </AppShell>
    );
  }

  if (!file) {
    return (
      <AppShell>
        <div className="py-20 text-center text-sm text-[#6f756f]">
          File not found.
        </div>
      </AppShell>
    );
  }

  const sizeDisplay =
    file.size_bytes >= 1024 * 1024
      ? `${(file.size_bytes / (1024 * 1024)).toFixed(1)} MB`
      : file.size_bytes >= 1024
        ? `${(file.size_bytes / 1024).toFixed(1)} KB`
        : `${file.size_bytes} B`;

  return (
    <AppShell>
      <div className="mb-4">
        <Link
          href="/files"
          className="inline-flex items-center gap-1 text-sm text-[#6f756f] hover:text-[#123d37]"
        >
          <ChevronLeft aria-hidden="true" size={16} />
          Back to Files
        </Link>
      </div>

      {/* File metadata card */}
      <section className="rounded-md border border-[#dcded8] bg-white p-6">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <FileText aria-hidden="true" className="text-[#275a53]" size={24} />
            <div>
              <h1 className="text-xl font-semibold">{file.name}</h1>
              <p className="mt-1 text-sm text-[#6f756f]">
                {file.file_type} · {sizeDisplay} · SHA256:{" "}
                {file.sha256.slice(0, 8)}…
              </p>
            </div>
          </div>
          <span className="rounded-md border border-[#dcded8] px-3 py-1 text-sm">
            {file.status}
          </span>
        </div>

        {actionStatus && (
          <p className="mt-3 text-sm text-[#275a53]">{actionStatus}</p>
        )}

        <div className="mt-4 flex flex-wrap gap-2">
          <button
            className="inline-flex items-center gap-1 rounded-md bg-[#123d37] px-3 py-2 text-xs font-semibold text-white"
            onClick={() => void handleParse()}
            type="button"
          >
            <Play aria-hidden="true" size={14} />
            Parse
          </button>
          <button
            className="inline-flex items-center gap-1 rounded-md border border-[#dcded8] px-3 py-2 text-xs font-semibold"
            onClick={() => void handleBuildChunks()}
            type="button"
          >
            <Boxes aria-hidden="true" size={14} />
            Build Chunks
          </button>
          <button
            className="inline-flex items-center gap-1 rounded-md border border-[#dcded8] px-3 py-2 text-xs font-semibold"
            onClick={() => void handleGenerateWiki()}
            type="button"
          >
            <BookOpenCheck aria-hidden="true" size={14} />
            Generate Wiki
          </button>
        </div>
      </section>

      {/* Document Blocks */}
      {blocks.length > 0 && (
        <section className="mt-4 rounded-md border border-[#dcded8] bg-white">
          <div className="border-b border-[#dcded8] px-4 py-3">
            <h2 className="text-base font-semibold">
              Document Blocks ({blocks.length})
            </h2>
          </div>
          <div className="divide-y divide-[#dcded8]">
            {blocks.map((block) => (
              <div key={block.id} className="px-4 py-3">
                <div className="mb-1 flex items-center gap-2">
                  <span className="rounded bg-[#f0f2ed] px-2 py-0.5 text-xs font-semibold text-[#6f756f]">
                    {block.block_type}
                  </span>
                  <span className="text-xs text-[#6f756f]">
                    #{block.block_index}
                  </span>
                  {block.page_number != null && (
                    <span className="text-xs text-[#6f756f]">
                      p.{block.page_number}
                    </span>
                  )}
                </div>
                <pre className="mt-1 max-h-40 overflow-auto whitespace-pre-wrap text-sm text-[#30342f]">
                  {block.raw_content}
                </pre>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Chunks */}
      {chunks.length > 0 && (
        <section className="mt-4 rounded-md border border-[#dcded8] bg-white">
          <div className="border-b border-[#dcded8] px-4 py-3">
            <h2 className="text-base font-semibold">
              Chunks ({chunks.length})
            </h2>
          </div>
          <div className="divide-y divide-[#dcded8]">
            {chunks.map((chunk) => (
              <div key={chunk.id} className="px-4 py-3">
                <div className="mb-1 flex items-center gap-2">
                  <span className="text-sm font-medium">
                    Chunk {chunk.chunk_index}
                  </span>
                  <span className="rounded-full bg-[#f0f2ed] px-2 py-0.5 text-xs text-[#6f756f]">
                    {chunk.status}
                  </span>
                  <span className="text-xs text-[#6f756f]">
                    {chunk.char_count} chars
                  </span>
                </div>
                <p className="text-sm text-[#30342f] line-clamp-3">
                  {chunk.search_text}
                </p>
              </div>
            ))}
          </div>
        </section>
      )}

      {blocks.length === 0 && chunks.length === 0 && (
        <section className="mt-4 rounded-md border border-[#dcded8] bg-white">
          <div className="grid min-h-48 place-items-center px-4 py-10 text-center">
            <div>
              <Boxes
                aria-hidden="true"
                className="mx-auto mb-3 text-[#275a53]"
                size={28}
              />
              <p className="text-sm font-medium">No content extracted yet</p>
              <p className="mt-1 max-w-md text-sm text-[#6f756f]">
                Parse the file to extract document blocks, then build chunks for
                retrieval.
              </p>
            </div>
          </div>
        </section>
      )}
    </AppShell>
  );
}
