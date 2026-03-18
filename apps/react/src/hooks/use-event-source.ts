import { useEffect, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";

/**
 * Subscribe to an SSE endpoint via native EventSource.
 * Invalidates the given query keys on every event.
 */
export function useEventSource(
  url: string,
  enabled: boolean,
  queryKeys: readonly (readonly unknown[])[],
) {
  const queryClient = useQueryClient();
  const stableKeys = useRef(queryKeys);
  stableKeys.current = queryKeys;

  useEffect(() => {
    if (!enabled) return;

    const es = new EventSource(url, { withCredentials: true });

    const invalidate = () => {
      for (const key of stableKeys.current) {
        void queryClient.invalidateQueries({ queryKey: key });
      }
    };

    // Handle named SSE events (video_progress, batch_progress)
    es.addEventListener("video_progress", invalidate);
    es.addEventListener("batch_progress", invalidate);
    // Fallback for unnamed events
    es.onmessage = invalidate;

    return () => es.close();
  }, [url, enabled, queryClient]);
}
