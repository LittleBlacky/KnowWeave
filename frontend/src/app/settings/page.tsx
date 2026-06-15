"use client";

import {AppShell} from "@/app-shell/AppShell";

export default function SettingsPage() {
  return (
    <AppShell>
      <div className="rounded-md border border-[#dcded8] bg-white p-6">
        <h1 className="text-xl font-semibold">Settings</h1>
        <p className="mt-2 text-sm text-[#6f756f]">
          KnowWeave P0 runs locally with Fake Provider by default. Configure
          environment variables for real LLM access.
        </p>

        <div className="mt-6 space-y-4">
          <div className="rounded-md border border-[#dcded8] p-4">
            <h2 className="text-base font-semibold">Provider</h2>
            <p className="mt-1 text-sm text-[#6f756f]">
              Current: Fake LLM Provider (no API key required). Set{" "}
              <code className="rounded bg-[#f0f2ed] px-1 text-xs">
                QWEN_API_KEY
              </code>{" "}
              in <code className="rounded bg-[#f0f2ed] px-1 text-xs">.env</code>{" "}
              to enable real Qwen.
            </p>
          </div>

          <div className="rounded-md border border-[#dcded8] p-4">
            <h2 className="text-base font-semibold">Storage</h2>
            <p className="mt-1 text-sm text-[#6f756f]">
              Files are stored locally in{" "}
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
            <h2 className="text-base font-semibold">Database</h2>
            <p className="mt-1 text-sm text-[#6f756f]">
              PostgreSQL 15 + pgvector via Docker Compose. Set{" "}
              <code className="rounded bg-[#f0f2ed] px-1 text-xs">
                DATABASE_URL
              </code>{" "}
              for custom connection.
            </p>
          </div>

          <div className="rounded-md border border-[#dcded8] p-4">
            <h2 className="text-base font-semibold">Upload Limits</h2>
            <p className="mt-1 text-sm text-[#6f756f]">
              Max upload size: configured via{" "}
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
