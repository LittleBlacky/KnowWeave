"use client";

import {Cpu, Globe, Key, Save, Zap} from "lucide-react";
import {useEffect, useState} from "react";
import {AppShell} from "@/app-shell/AppShell";
import {
  getSystemConfig,
  updateSystemConfig,
  type SystemConfig,
} from "@/shared/api/knowweave";
import {LoadingState, Badge} from "@/shared/ui";

export default function SettingsPage() {
  const [config, setConfig] = useState<SystemConfig | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  // Form state — all model config fields
  const [chatModel, setChatModel] = useState("");
  const [generationModel, setGenerationModel] = useState("");
  const [embeddingModel, setEmbeddingModel] = useState("");
  const [rerankModel, setRerankModel] = useState("");
  const [baseUrl, setBaseUrl] = useState("");

  useEffect(() => {
    getSystemConfig()
      .then((cfg) => {
        setConfig(cfg);
        setChatModel(cfg.models.chat);
        setGenerationModel(cfg.models.generation);
        setEmbeddingModel(cfg.models.embedding);
        setRerankModel(cfg.models.rerank);
        setBaseUrl(cfg.provider.base_url);
      })
      .catch((err) =>
        setError(err instanceof Error ? err.message : "加载配置失败"),
      );
  }, []);

  async function handleSave() {
    setSaving(true);
    setSaved(false);
    setError(null);
    try {
      const result = await updateSystemConfig({
        qwen_chat_model: chatModel || undefined,
        qwen_generation_model: generationModel || undefined,
        qwen_embedding_model: embeddingModel || undefined,
        qwen_rerank_model: rerankModel || undefined,
        qwen_base_url: baseUrl || undefined,
      });
      setConfig(result.config);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存失败");
    } finally {
      setSaving(false);
    }
  }

  const providerEnabled = config?.provider.qwen_enabled ?? false;

  return (
    <AppShell>
      <div className="mx-auto max-w-2xl space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold">模型配置</h1>
            <p className="mt-1 text-sm text-[#6f756f]">
              {providerEnabled
                ? "千问 API 已连接，可切换模型"
                : "未配置 API Key — 设置 QWEN_API_KEY 环境变量后启用"}
            </p>
          </div>
          <button
            className="inline-flex items-center gap-2 rounded-lg bg-[#123d37] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#0e2f2a] disabled:opacity-50"
            disabled={saving || !config}
            onClick={() => void handleSave()}
            type="button"
          >
            <Save aria-hidden="true" size={16} />
            {saving ? "保存中..." : saved ? "✓ 已保存" : "保存修改"}
          </button>
        </div>

        {error && (
          <div className="rounded-md border border-[#e8c8c5] bg-[#fdf4f3] px-4 py-3 text-sm text-[#a23b35]">
            {error}
          </div>
        )}

        {!config && !error && <LoadingState />}

        {config && (
          <>
            {/* Provider status card */}
            <div className="rounded-lg border border-[#dcded8] bg-white p-5">
              <div className="flex items-start gap-3">
                <div className="mt-0.5 rounded-md bg-[#f0f2ed] p-1.5">
                  <Globe
                    aria-hidden="true"
                    size={18}
                    className="text-[#275a53]"
                  />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h2 className="font-semibold">API 连接</h2>
                    <Badge tone={providerEnabled ? "accent" : "warning"}>
                      {providerEnabled ? "已启用" : "未启用"}
                    </Badge>
                  </div>
                  <div className="mt-3 space-y-2">
                    <FormField
                      label="Base URL"
                      value={baseUrl}
                      onChange={setBaseUrl}
                      placeholder="https://dashscope.aliyuncs.com/compatible-mode/v1"
                      icon={Globe}
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Models card */}
            <div className="rounded-lg border border-[#dcded8] bg-white p-5">
              <div className="flex items-start gap-3">
                <div className="mt-0.5 rounded-md bg-[#f0f2ed] p-1.5">
                  <Cpu
                    aria-hidden="true"
                    size={18}
                    className="text-[#275a53]"
                  />
                </div>
                <div className="flex-1">
                  <h2 className="font-semibold">模型设置</h2>
                  <p className="mb-4 text-sm text-[#6f756f]">
                    修改后在下次调用时生效
                  </p>
                  <div className="space-y-3">
                    <FormField
                      label="对话模型"
                      value={chatModel}
                      onChange={setChatModel}
                      disabled={!providerEnabled}
                      placeholder="qwen-plus / qwen-max / qwen-turbo"
                      icon={Zap}
                    />
                    <FormField
                      label="提取/生成模型"
                      value={generationModel}
                      onChange={setGenerationModel}
                      disabled={!providerEnabled}
                      placeholder="qwen-plus / qwen-max"
                      icon={Zap}
                    />
                    <FormField
                      label="Embedding 模型"
                      value={embeddingModel}
                      onChange={setEmbeddingModel}
                      disabled={!providerEnabled}
                      placeholder="text-embedding-v3"
                      icon={Zap}
                    />
                    <FormField
                      label="Rerank 模型"
                      value={rerankModel}
                      onChange={setRerankModel}
                      disabled={!providerEnabled}
                      placeholder="gte-rerank"
                      icon={Zap}
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Read-only info */}
            <div className="rounded-lg border border-[#dcded8] bg-white p-5">
              <div className="flex items-start gap-3">
                <div className="mt-0.5 rounded-md bg-[#f0f2ed] p-1.5">
                  <Key
                    aria-hidden="true"
                    size={18}
                    className="text-[#275a53]"
                  />
                </div>
                <div className="flex-1">
                  <h2 className="font-semibold">环境信息</h2>
                  <dl className="mt-3 space-y-1.5 text-sm">
                    {[
                      ["应用", config.app_name],
                      ["版本", config.version],
                      ["环境", config.environment],
                      ["超时", `${config.provider.timeout_seconds}s`],
                    ].map(([label, value]) => (
                      <div
                        key={label}
                        className="grid grid-cols-[100px_1fr] gap-2"
                      >
                        <dt className="text-[#6f756f]">{label}</dt>
                        <dd>{value}</dd>
                      </div>
                    ))}
                  </dl>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </AppShell>
  );
}

function FormField({
  label,
  value,
  onChange,
  disabled = false,
  placeholder = "",
  icon: Icon,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  placeholder?: string;
  icon?: React.ComponentType<{size?: number; className?: string}>;
}) {
  return (
    <label className="grid grid-cols-[120px_1fr] items-center gap-3 text-sm">
      <span className="flex items-center gap-1.5 text-[#6f756f]">
        {Icon && <Icon aria-hidden="true" size={14} />}
        {label}
      </span>
      <input
        className="rounded-md border border-[#dcded8] px-3 py-2 text-sm focus:border-[#275a53] focus:outline-none disabled:cursor-not-allowed disabled:bg-[#f0f2ed] disabled:text-[#b0b6ad]"
        disabled={disabled}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        type="text"
        value={value}
      />
    </label>
  );
}
