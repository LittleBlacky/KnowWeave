import type { LucideIcon } from "lucide-react";
import { Loader2 } from "lucide-react";

export function StatCard({
  label,
  value,
  detail,
  icon: Icon,
  tone = "neutral",
}: {
  label: string;
  value: string;
  detail?: string;
  icon?: LucideIcon;
  tone?: "neutral" | "warning" | "danger";
}) {
  const colorMap = {
    neutral: "text-[#275a53]",
    warning: "text-[#9a5a13]",
    danger: "text-[#a23b35]",
  };

  return (
    <article className="rounded-lg border border-[#dcded8] bg-white p-5 transition hover:border-[#b0b6ad]">
      <div className="mb-3 flex items-center justify-between">
        <span className="text-sm font-medium text-[#6f756f]">{label}</span>
        {Icon && <Icon aria-hidden="true" className={colorMap[tone]} size={18} />}
      </div>
      <div className="text-3xl font-bold tracking-tight text-[#161616]">
        {value}
      </div>
      {detail && (
        <div className="mt-2 text-sm text-[#6f756f]">{detail}</div>
      )}
    </article>
  );
}

export function StatCardSkeleton() {
  return (
    <article className="rounded-lg border border-[#dcded8] bg-white p-5">
      <div className="mb-3 flex items-center justify-between">
        <div className="h-4 w-16 animate-pulse rounded bg-[#f0f2ed]" />
        <div className="size-5 animate-pulse rounded bg-[#f0f2ed]" />
      </div>
      <div className="h-9 w-24 animate-pulse rounded bg-[#f0f2ed]" />
    </article>
  );
}
