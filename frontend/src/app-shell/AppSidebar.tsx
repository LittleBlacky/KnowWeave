"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { appRoutes } from "@/shared/config/routes";

export function AppSidebar() {
  const pathname = usePathname();

  return (
    <aside className="border-r border-[#dcded8] bg-[#ffffff] px-5 py-5 max-lg:border-b max-lg:border-r-0">
      <div className="mb-8 flex items-center gap-3">
        <div className="grid size-10 place-items-center rounded-md bg-[#123d37] text-sm font-semibold text-white">
          KW
        </div>
        <div>
          <div className="text-sm font-semibold">KnowWeave</div>
          <div className="text-xs text-[#6f756f]">P0 Workbench</div>
        </div>
      </div>
      <nav className="grid gap-1" aria-label="Primary">
        {appRoutes.map((item) => {
          const Icon = item.icon;
          const active =
            item.href === "/" ? pathname === item.href : pathname.startsWith(item.href);

          return (
            <Link
              aria-current={active ? "page" : undefined}
              className="flex items-center gap-2 rounded-md px-3 py-2 text-sm text-[#30342f] transition hover:bg-[#f0f2ed] aria-[current=page]:bg-[#e1ebe7] aria-[current=page]:text-[#123d37]"
              href={item.href}
              key={item.href}
            >
              <Icon aria-hidden="true" size={16} />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
