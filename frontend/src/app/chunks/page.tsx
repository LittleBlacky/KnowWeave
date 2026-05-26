import { AppShell } from "@/app-shell/AppShell";
import { ChunkWorkspace } from "@/features/chunk-workspace/ChunkWorkspace";

export default function ChunksPage() {
  return (
    <AppShell>
      <ChunkWorkspace />
    </AppShell>
  );
}
