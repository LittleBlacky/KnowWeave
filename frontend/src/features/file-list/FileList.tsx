"use client";

import {BookOpenCheck, Boxes, FileText, Play, Trash2} from "lucide-react";
import Link from "next/link";
import {useEffect, useState} from "react";

import {
  buildFileChunks,
  generateFileWiki,
  listFiles,
  parseFile,
  type KnowledgeFile,
} from "@/shared/api/knowweave";

type FileListProps = {
  refreshKey: number;
};

export function FileList({refreshKey}: FileListProps) {
  const [files, setFiles] = useState<KnowledgeFile[]>([]);
  const [statusByFile, setStatusByFile] = useState<Record<string, string>>({});

  async function refresh() {
    const response = await listFiles();
    setFiles(response.items);
  }

  useEffect(() => {
    // Client-side feature panels fetch their initial API state after mount.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void refresh();
  }, [refreshKey]);

  async function handleParse(file: KnowledgeFile) {
    setStatusByFile((current) => ({ ...current, [file.id]: "解析中" }));
    const result = await parseFile(file.id);
    setFiles((current) =>
      current.map((item) =>
        item.id === file.id ? {...item, status: result.status} : item,
      ),
    );
    setStatusByFile((current) => ({...current, [file.id]: result.status}));
  }

  async function handleBuildChunks(file: KnowledgeFile) {
    setStatusByFile((current) => ({...current, [file.id]: "Building chunks"}));
    const result = await buildFileChunks(file.id);
    setStatusByFile((current) => ({
      ...current,
      [file.id]: `${result.total} chunks built`,
    }));
  }

  async function handleGenerateWiki(file: KnowledgeFile) {
    setStatusByFile((current) => ({ ...current, [file.id]: "生成 Wiki 中" }));
    try {
      const wiki = await generateFileWiki(file.id);
      setStatusByFile((current) => ({
        ...current,
        [file.id]: `Wiki: ${wiki.title}`,
      }));
    } catch {
      setStatusByFile((current) => ({ ...current, [file.id]: "Wiki 生成失败" }));
    }
  }

  async function handleDelete(file: KnowledgeFile) {
    setStatusByFile((current) => ({ ...current, [file.id]: "删除中" }));
    await fetch(`/api/v1/files/${file.id}`, {method: "DELETE"});
    setFiles((current) => current.filter((f) => f.id !== file.id));
  }

  return (
    <section className="rounded-md border border-[#dcded8] bg-white">
      <div className="flex items-center justify-between border-b border-[#dcded8] px-4 py-3">
        <h2 className="text-base font-semibold">知识文件</h2>
        <span className="text-sm text-[#6f756f]">{files.length} 个文件</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-left text-sm">
          <thead className="bg-[#f0f2ed] text-[#30342f]">
            <tr>
              <th className="px-4 py-3 font-semibold">文件</th>
              <th className="px-4 py-3 font-semibold">类型</th>
              <th className="px-4 py-3 font-semibold">状态</th>
              <th className="px-4 py-3 font-semibold">大小</th>
              <th className="px-4 py-3 font-semibold">操作</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#dcded8]">
            {files.map((file) => (
              <tr key={file.id}>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <FileText
                      aria-hidden="true"
                      className="text-[#275a53]"
                      size={16}
                    />
                    <Link
                      href={`/files/${file.id}`}
                      className="font-medium text-[#123d37] hover:underline"
                    >
                      {file.name}
                    </Link>
                  </div>
                </td>
                <td className="px-4 py-3">{file.file_type}</td>
                <td className="px-4 py-3">
                  <span className="rounded-md border border-[#dcded8] px-2 py-1 text-xs">
                    {statusByFile[file.id] ?? file.status}
                  </span>
                </td>
                <td className="px-4 py-3">{file.size_bytes} B</td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-2">
                    <button
                      aria-label={`解析 ${file.name}`}
                      className="inline-flex items-center gap-1 rounded-md bg-[#123d37] px-3 py-2 text-xs font-semibold text-white"
                      onClick={() => void handleParse(file)}
                      type="button"
                    >
                      <Play aria-hidden="true" size={14} />
                      解析
                    </button>
                    <button
                      aria-label={`构建分块 ${file.name}`}
                      className="inline-flex items-center gap-1 rounded-md border border-[#dcded8] px-3 py-2 text-xs font-semibold"
                      onClick={() => void handleBuildChunks(file)}
                      type="button"
                    >
                      <Boxes aria-hidden="true" size={14} />
                      分块
                    </button>
                    <button
                      aria-label={`生成 Wiki ${file.name}`}
                      className="inline-flex items-center gap-1 rounded-md border border-[#dcded8] px-3 py-2 text-xs font-semibold"
                      onClick={() => void handleGenerateWiki(file)}
                      type="button"
                    >
                      <BookOpenCheck aria-hidden="true" size={14} />
                      Wiki
                    </button>
                    <button
                      aria-label={`删除 ${file.name}`}
                      className="inline-flex items-center gap-1 rounded-md border border-[#dcded8] px-2 py-2 text-xs font-semibold text-red-600 hover:bg-red-50"
                      onClick={() => void handleDelete(file)}
                      type="button"
                    >
                      <Trash2 aria-hidden="true" size={14} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

