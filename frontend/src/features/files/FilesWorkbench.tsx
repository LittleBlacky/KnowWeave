"use client";

import { useState } from "react";

import { FileList } from "@/features/file-list/FileList";
import { FileUpload } from "@/features/file-upload/FileUpload";

export function FilesWorkbench() {
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <div className="grid gap-4">
      <FileUpload onUploaded={() => setRefreshKey((current) => current + 1)} />
      <FileList refreshKey={refreshKey} />
    </div>
  );
}
