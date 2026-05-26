"use client";

import { usePathname } from "next/navigation";

import { routeLabelForPath } from "@/shared/config/routes";

export function RouteBreadcrumbs() {
  const pathname = usePathname();
  const label = routeLabelForPath(pathname);

  return (
    <nav aria-label="Breadcrumb" className="text-xs font-semibold uppercase text-[#275a53]">
      Dashboard / {label}
    </nav>
  );
}
