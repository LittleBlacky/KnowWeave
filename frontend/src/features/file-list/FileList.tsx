"use client";

import { BookOpenCheck, Boxes, FileText, Play, Trash2 } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { buildFileChunks, generateFileWiki, listFiles, parseFile, type KnowledgeFile } from "@/shared/api/knowweave";
import { Badge } from "@/shared/ui";

type FileListProps = { refreshKey: number };

export function FileList({ refreshKey }: FileListProps) {
  const [files, setFiles] = useState<KnowledgeFile[]>([]);
  const [statusByFile, setStatusByFile] = useState<Record<string, string>>({});

  async function refresh() {
    const response = await listFiles();
    setFiles(response.items);
  }

  useEffect(() => {
    void refresh();
  }, [refreshKey]);

  async function handleParse(file: KnowledgeFile) {
    setStatusByFile((c) => ({ ...c, [file.id]: "解析中" }));
    const result = await parseFile(file.id);
    setFiles((c) => c.map((f) => (f.id === file.id ? { ...f, status: result.status } : f)));
    setStatusByFile((c) => ({ ...c, [file.id]: result.status }));
  }

  async function handleBuildChunks(file: KnowledgeFile) {
    setStatusByFile((c) => ({ ...c, [file.id]: "构建分块中" }));
    const result = await buildFileChunks(file.id);
    setStatusByFile((c) => ({ ...c, [file.id]: `${result.total} 个分块` }));
  }

  async function handleGenerateWiki(file: KnowledgeFile) {
    setStatusByFile((c) => ({ ...c, [file.id]: "生成 Wiki 中" }));
    try {
      const wiki = await generateFileWiki(file.id);
      setStatusByFile((c) => ({ ...c, [file.id]: `Wiki: ${wiki.title}` }));
    } catch {
      setStatusByFile((c) => ({ ...c, [file.id]: "Wiki 生成失败" }));
    }
  }

  async function handleDelete(file: KnowledgeFile) {
    setStatusByFile((c) => ({ ...c, [file.id]: "删除中" }));
    await fetch(`/api/v1/files/${file.id}`, { method: "DELETE" });
    setFiles((c) => c.filter((f) => f.id !== file.id));
  }

  const statusTone = (s: string) =>
    s === "parse_succeeded" ? "accent" : s === "parse_failed" ? "danger" : "neutral";

  return (
    <section className="rounded-lg border border-[#dcded8] bg-white">
      <div className="flex items-center justify-between border-b border-[#dcded8] px-5 py-3">
        <h2 className="text-base font-semibold">知识文件</h2>
        <span className="text-sm text-[#6f756f]">{files.length} 个文件</span>
      </div>

      {files.length === 0 ? (
        <div className="grid place-items-center py-16 text-center">
          <FileText aria-hidden="true" className="mx-auto mb-3 text-[#b0b6ad]" size={36} />
          <p className="text-sm font-medium text-[#30342f]">暂无文件</p>
          <p className="mt-1 text-sm text-[#6f756f]">上传文件以开始知识治理流程。</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-left text-sm">
            <thead className="border-b border-[#dcded8] bg-[#f7f7f5]">
              <tr>
                <th className="px-5 py-3 text-xs font-semibold text-[#6f756f]">文件</th>
                <th className="px-5 py-3 text-xs font-semibold text-[#6f756f]">类型</th>
                <th className="px-5 py-3 text-xs font-semibold text-[#6f756f]">状态</th>
                <th className="px-5 py-3 text-xs font-semibold text-[#6f756f]">大小</th>
                <th className="px-5 py-3 text-xs font-semibold text-[#6f756f]">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#dcded8]">
              {files.map((file) => (
                <tr key={file.id} className="transition hover:bg-[#f7f7f5]">
                  <td className="px-5 py-3">
                    <div className="flex items-center gap-2">
                      <FileText aria-hidden="true" className="text-[#275a53]" size={16} />
                      <Link
                        href={`/files/${file.id}`}
                        className="font-medium text-[#123d37] hover:underline"
                      >
                        {file.name}
                      </Link>
                    </div>
                  </td>
                  <td className="px-5 py-3">
                    <span className="text-[#6f756f]">
                      {file.file_type?.toUpperCase() ?? "—"}
                    </span>
                  </td>
                  <td className="px-5 py-3">
                    <div className="flex items-center gap-2">
                      <Badge tone={statusTone(file.status)}>{file.status}</Badge>
                      {statusByFile[file.id] && (
                        <span className="text-xs text-[#6f756f]">{statusByFile[file.id]}</span>
                      )}
                    </div>
                  </td>
                  <td className="px-5 py-3 text-[#6f756f]">
                    {file.size_bytes ? `${(file.size_bytes / 1024).toFixed(1)} KB` : "—"}
                  </td>
                  <td className="px-5 py-3">
                    <div className="flex items-center gap-1.5">
                      <button
                        className="inline-flex items-center gap-1 rounded border border-[#dcded8] px-2.5 py-1.5 text-xs font-semibold transition hover:bg-[#f0f2ed]"
                        onClick={() => void handleParse(file)}
                        type="button"
                      >
                        <Play aria-hidden="true" size={12} />解析
                      </button>
                      <button
                        className="inline-flex items-center gap-1 rounded border border-[#dcded8] px-2.5 py-1.5 text-xs font-semibold transition hover:bg-[#f0f2ed]"
                        onClick={() => void handleBuildChunks(file)}
                        type="button"
                      >
                        <Boxes aria-hidden="true" size={12} />分块
                      </button>
                      <button
                        className="inline-flex items-center gap-1 rounded border border-[#dcded8] px-2.5 py-1.5 text-xs font-semibold transition hover:bg-[#f0f2ed]"
                        onClick={() => void handleGenerateWiki(file)}
                        type="button"
                      >
                        <BookOpenCheck aria-hidden="true" size={12} />Wiki
                      </button>
                      <button
                        className="inline-flex items-center gap-1 rounded border border-[#e8c8c5] px-2.5 py-1.5 text-xs font-semibold text-[#a23b35] transition hover:bg-[#fdf4f3]"
                        onClick={() => void handleDelete(file)}
                        type="button"
                      >
                        <Trash2 aria-hidden="true" size={12} />删除
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
