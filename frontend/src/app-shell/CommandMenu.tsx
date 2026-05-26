import { Search } from "lucide-react";

export function CommandMenu() {
  return (
    <button
      className="flex items-center gap-2 rounded-md border border-[#dcded8] bg-white px-3 py-2 text-sm text-[#30342f]"
      type="button"
    >
      <Search aria-hidden="true" size={16} />
      <span>Search files, chunks, wiki</span>
    </button>
  );
}
