"use client";

import { useEffect, useState } from "react";
import JobDescriptionEditor from "@/components/job-description-editor";

export function ClientJobEditor() {
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  if (!isMounted) {
    // Return a placeholder that matches the server-rendered layout
    return (
      <div className="h-full flex flex-col bg-card text-card-foreground rounded-lg border animate-pulse">
        <div className="p-6 pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-5 h-5 bg-muted rounded"></div>
              <div className="w-32 h-6 bg-muted rounded"></div>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-20 h-6 bg-muted rounded-full"></div>
              <div className="w-12 h-6 bg-muted rounded-full"></div>
            </div>
          </div>
        </div>
        <div className="flex-1 p-6 pt-0">
          <div className="h-10 bg-muted rounded mb-4"></div>
          <div className="space-y-4">
            <div className="h-10 bg-muted rounded"></div>
            <div className="h-10 bg-muted rounded"></div>
            <div className="h-32 bg-muted rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  return <JobDescriptionEditor />;
}

export default ClientJobEditor;