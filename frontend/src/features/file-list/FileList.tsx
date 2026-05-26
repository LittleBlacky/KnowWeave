"use client";

import { Boxes, FileText, Play } from "lucide-react";
import { useEffect, useState } from "react";

import {
  buildFileChunks,
  listFiles,
  parseFile,
  type KnowledgeFile,
} from "@/shared/api/knowweave";

type FileListProps = {
  refreshKey: number;
};

export function FileList({ refreshKey }: FileListProps) {
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
    setStatusByFile((current) => ({ ...current, [file.id]: "Parsing" }));
    const result = await parseFile(file.id);
    setFiles((current) =>
      current.map((item) => (item.id === file.id ? { ...item, status: result.status } : item)),
    );
    setStatusByFile((current) => ({ ...current, [file.id]: result.status }));
  }

  async function handleBuildChunks(file: KnowledgeFile) {
    setStatusByFile((current) => ({ ...current, [file.id]: "Building chunks" }));
    const result = await buildFileChunks(file.id);
    setStatusByFile((current) => ({ ...current, [file.id]: `${result.total} chunks built` }));
  }

  return (
    <section className="rounded-md border border-[#dcded8] bg-white">
      <div className="flex items-center justify-between border-b border-[#dcded8] px-4 py-3">
        <h2 className="text-base font-semibold">Evidence Files</h2>
        <span className="text-sm text-[#6f756f]">{files.length} files</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-left text-sm">
          <thead className="bg-[#f0f2ed] text-[#30342f]">
            <tr>
              <th className="px-4 py-3 font-semibold">File</th>
              <th className="px-4 py-3 font-semibold">Type</th>
              <th className="px-4 py-3 font-semibold">Status</th>
              <th className="px-4 py-3 font-semibold">Size</th>
              <th className="px-4 py-3 font-semibold">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#dcded8]">
            {files.map((file) => (
              <tr key={file.id}>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <FileText aria-hidden="true" className="text-[#275a53]" size={16} />
                    <span className="font-medium">{file.name}</span>
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
                      aria-label={`Parse ${file.name}`}
                      className="inline-flex items-center gap-1 rounded-md bg-[#123d37] px-3 py-2 text-xs font-semibold text-white"
                      onClick={() => void handleParse(file)}
                      type="button"
                    >
                      <Play aria-hidden="true" size={14} />
                      Parse
                    </button>
                    <button
                      aria-label={`Build chunks for ${file.name}`}
                      className="inline-flex items-center gap-1 rounded-md border border-[#dcded8] px-3 py-2 text-xs font-semibold"
                      onClick={() => void handleBuildChunks(file)}
                      type="button"
                    >
                      <Boxes aria-hidden="true" size={14} />
                      Chunks
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
