"use client";

import { useEffect, useState, type ReactNode } from "react";

import { enableMocks } from "@/shared/config/env";

type MockProviderProps = {
  children: ReactNode;
};

export function MockProvider({ children }: MockProviderProps) {
  const [ready, setReady] = useState(!enableMocks);

  useEffect(() => {
    if (!enableMocks) {
      return;
    }

    let active = true;
    import("@/test/browser")
      .then(({ worker }) =>
        worker.start({
          onUnhandledRequest: "bypass",
          serviceWorker: { url: "/mockServiceWorker.js" },
        }),
      )
      .finally(() => {
        if (active) {
          setReady(true);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  return ready ? children : null;
}
