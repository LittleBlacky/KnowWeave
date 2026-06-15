"use client";

import {Upload} from "lucide-react";
import {useRef, useState} from "react";

import {uploadFile, type KnowledgeFile} from "@/shared/api/knowweave";

type FileUploadProps = {
  onUploaded?: (file: KnowledgeFile) => void;
};

export function FileUpload({onUploaded}: FileUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [message, setMessage] = useState<string>("Ready");
  const [busy, setBusy] = useState(false);

  async function handleFile(file: File | undefined) {
    if (!file) {
      return;
    }
    setBusy(true);
    setMessage("Uploading");
    try {
      const created = await uploadFile(file);
      setMessage(`Uploaded ${created.name}`);
      onUploaded?.(created);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Upload failed");
    } finally {
      setBusy(false);
      if (inputRef.current) {
        inputRef.current.value = "";
      }
    }
  }

  return (
    <section className="rounded-md border border-[#dcded8] bg-white p-4">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold">上传知识文件</h2>
          <p className="mt-1 text-sm text-[#6f756f]">
            支持 txt、md、pdf、docx 格式。
          </p>
        </div>
        <Upload aria-hidden="true" className="text-[#275a53]" size={20} />
      </div>
      <label className="block text-sm font-medium" htmlFor="evidence-file">
        上传知识文件
      </label>
      <input
        accept=".txt,.md,.markdown,.pdf,.docx"
        className="mt-2 w-full rounded-md border border-[#dcded8] bg-[#f7f7f5] px-3 py-2 text-sm"
        disabled={busy}
        id="evidence-file"
        onChange={(event) => void handleFile(event.target.files?.[0])}
        ref={inputRef}
        type="file"
      />
      <div className="mt-3 text-sm text-[#275a53]" role="status">
        {message}
      </div>
    </section>
  );
}

