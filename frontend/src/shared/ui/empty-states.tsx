import { FileText, Inbox, Loader2, AlertTriangle } from "lucide-react";
import type { ReactNode } from "react";

export function EmptyState({
  icon: Icon = Inbox,
  title,
  description,
  children,
}: {
  icon?: typeof Inbox;
  title: string;
  description?: string;
  children?: ReactNode;
}) {
  return (
    <div className="grid min-h-72 place-items-center px-4 py-12 text-center">
      <div>
        <Icon
          aria-hidden="true"
          className="mx-auto mb-4 text-[#b0b6ad]"
          size={36}
        />
        <p className="text-sm font-semibold text-[#30342f]">{title}</p>
        {description && (
          <p className="mt-1 max-w-sm text-sm text-[#6f756f]">{description}</p>
        )}
        {children && <div className="mt-4">{children}</div>}
      </div>
    </div>
  );
}

export function LoadingState({ text = "加载中…" }: { text?: string }) {
  return (
    <div className="flex items-center justify-center gap-3 py-20">
      <Loader2 aria-hidden="true" className="animate-spin text-[#275a53]" size={28} />
      <span className="text-sm text-[#6f756f]">{text}</span>
    </div>
  );
}

export function ErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div className="grid min-h-72 place-items-center px-4 py-12 text-center">
      <div>
        <AlertTriangle
          aria-hidden="true"
          className="mx-auto mb-4 text-[#a23b35]"
          size={36}
        />
        <p className="text-sm font-semibold text-[#a23b35]">加载失败</p>
        <p className="mt-1 max-w-sm text-sm text-[#6f756f]">{message}</p>
        {onRetry && (
          <button
            className="mt-4 rounded-md bg-[#123d37] px-4 py-2 text-sm font-semibold text-white"
            onClick={onRetry}
            type="button"
          >
            重试
          </button>
        )}
      </div>
    </div>
  );
}
