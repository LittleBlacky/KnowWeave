import type { SourceSpan } from "@/shared/api/knowweave";

type SourceLocatorPanelProps = {
  source?: SourceSpan;
};

export function SourceLocatorPanel({ source }: SourceLocatorPanelProps) {
  return (
    <div className="rounded-md border border-[#dcded8] bg-[#f0f2ed] p-3 text-sm">
      <div className="mb-1 font-semibold">Source locator</div>
      <div>{formatLocator(source)}</div>
      <p className="mt-2 text-[#5d645d]">{source?.preview_text ?? "Source preview unavailable."}</p>
    </div>
  );
}

function formatLocator(source: SourceSpan | undefined) {
  if (!source) {
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
