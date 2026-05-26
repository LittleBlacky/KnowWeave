import type { SourceSpan } from "@/shared/api/knowweave";

export type SourceLocator = SourceSpan & {
  source_available?: boolean;
  source_label?: string | null;
  source_type?: string | null;
};

type SourceLocatorPanelProps = {
  source?: SourceLocator;
};

export function SourceLocatorPanel({ source }: SourceLocatorPanelProps) {
  const sourceAvailable = source?.source_available ?? Boolean(source);

  return (
    <div className="rounded-md border border-[#dcded8] bg-[#f0f2ed] p-3 text-sm">
      <div className="mb-2 flex items-center justify-between gap-2">
        <div>
          <div className="font-semibold">Source locator</div>
          {source?.source_label ? <div className="text-xs text-[#5d645d]">{source.source_label}</div> : null}
        </div>
        <span className="rounded-md border border-[#cfd6cf] bg-white px-2 py-1 text-xs">
          {sourceAvailable ? "Available" : "Snapshot only"}
        </span>
      </div>
      <div>{formatLocator(source, sourceAvailable)}</div>
      <p className="mt-2 text-[#5d645d]">{source?.preview_text ?? "Source preview unavailable."}</p>
      <button
        className="mt-3 rounded-md bg-[#123d37] px-3 py-2 text-xs font-semibold text-white disabled:cursor-not-allowed disabled:bg-[#c9cdc7] disabled:text-[#5d645d]"
        disabled={!sourceAvailable}
        type="button"
      >
        Open source
      </button>
    </div>
  );
}

function formatLocator(source: SourceLocator | undefined, sourceAvailable: boolean) {
  if (!source || !sourceAvailable) {
    return "Source unavailable";
  }
  if (source.line_start && source.line_end) {
    return `Lines ${source.line_start}-${source.line_end}`;
  }
  if (source.page_number) {
    return `Page ${source.page_number}`;
  }
  return "Block source";
}
