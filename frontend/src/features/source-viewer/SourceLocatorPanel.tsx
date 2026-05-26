import type { SourceSpan } from "@/shared/api/knowweave";
import Link from "next/link";

export type SourceLocator = SourceSpan & {
  file_id?: string | null;
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
      {sourceAvailable ? (
        <Link
          className="mt-3 inline-block rounded-md bg-[#123d37] px-3 py-2 text-xs font-semibold text-white"
          href={sourceHref(source)}
        >
          Open source
        </Link>
      ) : (
        <button
          className="mt-3 rounded-md bg-[#c9cdc7] px-3 py-2 text-xs font-semibold text-[#5d645d]"
          disabled
          type="button"
        >
          Open source
        </button>
      )}
    </div>
  );
}

function sourceHref(source: SourceLocator | undefined) {
  const params = new URLSearchParams();
  if (source?.file_id) {
    params.set("file_id", source.file_id);
  }
  if (source?.id) {
    params.set("source_span_id", source.id);
  }
  if (source?.page_number) {
    params.set("page", String(source.page_number));
  }
  if (source?.line_start) {
    params.set("line_start", String(source.line_start));
  }
  if (source?.line_end) {
    params.set("line_end", String(source.line_end));
  }
  const query = params.toString();
  return query ? `/files?${query}` : "/files";
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
