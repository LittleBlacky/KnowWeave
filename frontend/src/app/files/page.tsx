import { AppShell } from "@/app-shell/AppShell";
import { FilesWorkbench } from "@/features/files/FilesWorkbench";

export default function FilesPage() {
  return (
    <AppShell>
      <FilesWorkbench />
    </AppShell>
  );
}
