import { AppShell } from "@/app-shell/AppShell";
import { WikiPage } from "@/features/wiki/WikiPage";

export default function Page() {
  return (
    <AppShell>
      <WikiPage />
    </AppShell>
  );
}
