import type { LucideIcon } from "lucide-react";
import {
  BookOpenCheck,
  Boxes,
  FileText,
  Gauge,
  MessageSquareText,
  Network,
  Search,
  Settings,
  Tags,
} from "lucide-react";

export type AppRoute = {
  label: string;
  href: string;
  icon: LucideIcon;
  p0: boolean;
};

export const appRoutes: AppRoute[] = [
  { label: "Dashboard", href: "/", icon: Gauge, p0: true },
  { label: "Files", href: "/files", icon: FileText, p0: true },
  { label: "Chunks", href: "/chunks", icon: Boxes, p0: true },
  { label: "Knowledge Units", href: "/knowledge-units", icon: Network, p0: true },
  { label: "Wiki", href: "/wiki", icon: BookOpenCheck, p0: true },
  { label: "Search", href: "/search", icon: Search, p0: true },
  { label: "Chat", href: "/chat", icon: MessageSquareText, p0: true },
  { label: "Evaluation", href: "/evaluation", icon: Tags, p0: false },
  { label: "Settings", href: "/settings", icon: Settings, p0: false },
];

export function routeLabelForPath(pathname: string): string {
  const exactMatch = appRoutes.find((route) => route.href === pathname);
  if (exactMatch) {
    return exactMatch.label;
  }

  const parentMatch = appRoutes
    .filter((route) => route.href !== "/" && pathname.startsWith(`${route.href}/`))
    .sort((a, b) => b.href.length - a.href.length)[0];

  return parentMatch?.label ?? "Dashboard";
}
