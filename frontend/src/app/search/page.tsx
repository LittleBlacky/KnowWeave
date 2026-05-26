import { AppShell } from "@/app-shell/AppShell";
import { SearchPage } from "@/features/search/SearchPage";

export default function SearchRoute() {
  return (
    <AppShell>
      <SearchPage />
    </AppShell>
  );
}
