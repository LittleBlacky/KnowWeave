import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

/** Left-side scrollable list panel for list+detail layouts */
export function ListPanel({
  title,
  icon: Icon,
  count,
  children,
}: {
  title: string;
  icon?: LucideIcon;
  count?: number;
  children: ReactNode;
}) {
  return (
    <section className="flex flex-col rounded-lg border border-[#dcded8] bg-white max-h-[calc(100vh-12rem)]">
      <div className="flex shrink-0 items-center justify-between border-b border-[#dcded8] px-4 py-3">
        <div className="flex items-center gap-2">
          {Icon && <Icon aria-hidden="true" className="text-[#275a53]" size={18} />}
          <h2 className="text-base font-semibold">{title}</h2>
        </div>
        {count !== undefined && (
          <span className="rounded-full bg-[#f0f2ed] px-2.5 py-0.5 text-xs font-medium text-[#6f756f]">
            {count}
          </span>
        )}
      </div>
      <div className="flex-1 overflow-y-auto p-3">{children}</div>
    </section>
  );
}

/** Right-side detail panel for list+detail layouts */
export function DetailPanel({
  title,
  children,
  actions,
}: {
  title?: string;
  children: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <section className="flex flex-col rounded-lg border border-[#dcded8] bg-white max-h-[calc(100vh-12rem)]">
      {(title || actions) && (
        <div className="flex shrink-0 items-center justify-between border-b border-[#dcded8] px-4 py-3">
          {title && <h2 className="text-base font-semibold">{title}</h2>}
          {actions}
        </div>
      )}
      <div className="flex-1 overflow-y-auto p-4">{children}</div>
    </section>
  );
}

/** Clickable list item card (for use inside ListPanel) */
export function ListItemCard({
  active,
  onClick,
  title,
  subtitle,
  status,
  tags,
}: {
  active?: boolean;
  onClick?: () => void;
  title: string;
  subtitle?: string;
  status?: string;
  tags?: { id: string; name: string }[];
}) {
  const Comp = onClick ? "button" : "div";
  return (
    <Comp
      aria-pressed={active}
      className="w-full rounded-md border border-[#dcded8] p-3.5 text-left transition hover:border-[#275a53] aria-pressed:border-[#275a53] aria-pressed:bg-[#f0f6f3]"
      onClick={onClick}
      type={onClick ? "button" : undefined}
    >
      <div className="mb-1.5 flex items-start justify-between gap-2">
        <h3 className="text-sm font-semibold leading-snug">{title}</h3>
        {status && (
          <span className="shrink-0 rounded border border-[#dcded8] px-1.5 py-0.5 text-xs text-[#6f756f]">
            {status}
          </span>
        )}
      </div>
      {subtitle && (
        <p className="line-clamp-2 text-sm text-[#5d645d]">{subtitle}</p>
      )}
      {tags && tags.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {tags.map((tag) => (
            <span
              className="rounded bg-[#e1ebe7] px-2 py-0.5 text-xs font-medium text-[#123d37]"
              key={tag.id}
            >
              {tag.name}
            </span>
          ))}
        </div>
      )}
    </Comp>
  );
}
