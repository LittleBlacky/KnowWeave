"use client";

import {useState} from "react";

import {FileList} from "@/features/file-list/FileList";
import {FileUpload} from "@/features/file-upload/FileUpload";
import {
  parseFile,
  buildFileChunks,
  generateFileWiki,
  autoGenerateKnowledgeUnits,
  type KnowledgeFile,
} from "@/shared/api/knowweave";

export function FilesWorkbench() {
  const [refreshKey, setRefreshKey] = useState(0);
  const [pipelineStatus, setPipelineStatus] = useState("");

  async function handleUploaded(file: KnowledgeFile) {
    setPipelineStatus(`正在解析 ${file.name}…`);
    try {
      await parseFile(file.id);
      setPipelineStatus(`正在构建分块 ${file.name}…`);
      const chunkResult = await buildFileChunks(file.id);
      if (chunkResult.total > 0) {
        setPipelineStatus(`正在生成知识单元 ${file.name}…`);
        await autoGenerateKnowledgeUnits(file.id);
        setPipelineStatus(`正在生成 Wiki ${file.name}…`);
        await generateFileWiki(file.id);
      }
      setPipelineStatus(`${file.name} 处理完成: ${chunkResult.total} 个分块`);
    } catch (err) {
      setPipelineStatus(
        `处理中断: ${err instanceof Error ? err.message : "未知错误"}`,
      );
    }
    setRefreshKey((current) => current + 1);
  }

  return (
    <div className="grid gap-4">
      <FileUpload onUploaded={(file) => void handleUploaded(file)} />
      {pipelineStatus && (
        <div className="rounded-md border border-[#dcded8] bg-[#e1ebe7] px-4 py-3 text-sm text-[#123d37]">
          {pipelineStatus}
        </div>
      )}
      <FileList refreshKey={refreshKey} />
    </div>
  );
}

