import type { LucideIcon } from "lucide-react";
import {
  BookOpenCheck,
  Boxes,
  FileText,
  Gauge,
  Lightbulb,
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
  { label: "仪表盘", href: "/", icon: Gauge, p0: true },
  { label: "文件管理", href: "/files", icon: FileText, p0: true },
  { label: "知识分块", href: "/chunks", icon: Boxes, p0: true },
  { label: "知识单元", href: "/knowledge-units", icon: Network, p0: true },
  { label: "Wiki", href: "/wiki", icon: BookOpenCheck, p0: true },
  { label: "搜索", href: "/search", icon: Search, p0: true },
  { label: "AI 问答", href: "/chat", icon: MessageSquareText, p0: true },
  { label: "评测", href: "/evaluation", icon: Tags, p0: false },
  { label: "策展", href: "/curation", icon: Lightbulb, p0: false },
  { label: "设置", href: "/settings", icon: Settings, p0: false },
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
