import { AppShell } from "@/app-shell/AppShell";
import { TagManager } from "@/features/tags/TagManager";

export default function Page() {
  return (
    <AppShell>
      <TagManager />
    </AppShell>
  );
}
