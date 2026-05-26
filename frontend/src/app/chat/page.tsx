import { AppShell } from "@/app-shell/AppShell";
import { ChatPage } from "@/features/chat/ChatPage";

export default function ChatRoute() {
  return (
    <AppShell>
      <ChatPage />
    </AppShell>
  );
}
