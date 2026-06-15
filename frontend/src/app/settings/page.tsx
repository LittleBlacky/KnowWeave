"use client";

import {AppShell} from "@/app-shell/AppShell";

export default function SettingsPage() {
  return (
    <AppShell>
      <div className="rounded-md border border-[#dcded8] bg-white p-6">
        <h1 className="text-xl font-semibold">设置</h1>
        <p className="mt-2 text-sm text-[#6f756f]">
          KnowWeave P0 默认使用 Fake Provider 在本地运行。
          配置环境变量以接入真实 LLM。
        </p>

        <div className="mt-6 space-y-4">
          <div className="rounded-md border border-[#dcded8] p-4">
            <h2 className="text-base font-semibold">模型提供商</h2>
            <p className="mt-1 text-sm text-[#6f756f]">
              当前: Fake LLM Provider（无需 API Key）。 Set{" "}
              <code className="rounded bg-[#f0f2ed] px-1 text-xs">
                QWEN_API_KEY
              </code>{" "}
              in <code className="rounded bg-[#f0f2ed] px-1 text-xs">.env</code>{" "}
              to enable real Qwen.
            </p>
          </div>

          <div className="rounded-md border border-[#dcded8] p-4">
            <h2 className="text-base font-semibold">存储</h2>
            <p className="mt-1 text-sm text-[#6f756f]">
              文件存储在本地{" "}
              <code className="rounded bg-[#f0f2ed] px-1 text-xs">
                data/files/
              </code>
              . Configure{" "}
              <code className="rounded bg-[#f0f2ed] px-1 text-xs">
                FILE_STORAGE_ROOT
              </code>{" "}
              to change.
            </p>
          </div>

          <div className="rounded-md border border-[#dcded8] p-4">
            <h2 className="text-base font-semibold">数据库</h2>
            <p className="mt-1 text-sm text-[#6f756f]">
              PostgreSQL 15 + pgvector，通过 Docker Compose 启动。 Set{" "}
              <code className="rounded bg-[#f0f2ed] px-1 text-xs">
                DATABASE_URL
              </code>{" "}
              for custom connection.
            </p>
          </div>

          <div className="rounded-md border border-[#dcded8] p-4">
            <h2 className="text-base font-semibold">上传限制</h2>
            <p className="mt-1 text-sm text-[#6f756f]">
              最大上传大小: 通过{" "}
              <code className="rounded bg-[#f0f2ed] px-1 text-xs">
                MAX_UPLOAD_MB
              </code>{" "}
              (default 50 MB). Supported formats: txt, md, pdf, docx.
            </p>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
