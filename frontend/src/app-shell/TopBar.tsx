import { CommandMenu } from "./CommandMenu";
import { RouteBreadcrumbs } from "./RouteBreadcrumbs";

export function TopBar() {
  return (
    <header className="mb-6 flex items-start justify-between gap-4 max-md:block">
      <div>
        <RouteBreadcrumbs />
        <h1 className="mt-2 text-2xl font-semibold tracking-normal text-[#161616]">
          Evidence Governance Overview
        </h1>
      </div>
      <div className="max-md:mt-4">
        <CommandMenu />
      </div>
    </header>
  );
}
