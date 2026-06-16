import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

export function PageHeader({
  title,
  description,
  children,
  icon: Icon,
}: {
  title: string;
  description?: string;
  children?: ReactNode;
  icon?: LucideIcon;
}) {
  return (
    <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
      <div className="flex items-start gap-3">
        {Icon && (
          <div className="mt-0.5 grid size-9 place-items-center rounded-lg bg-[#e1ebe7] text-[#123d37]">
            <Icon aria-hidden="true" size={18} />
          </div>
        )}
        <div>
          <h1 className="text-xl font-semibold text-[#161616]">{title}</h1>
          {description && (
            <p className="mt-1 text-sm text-[#6f756f]">{description}</p>
          )}
        </div>
      </div>
      {children && <div className="flex items-center gap-3">{children}</div>}
    </div>
  );
}
