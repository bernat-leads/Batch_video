import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook } from "@testing-library/react";
import { useEventSource } from "./use-event-source";

// ---------------------------------------------------------------------------
// Mock EventSource
// ---------------------------------------------------------------------------

interface MockEventSourceInstance {
  url: string;
  withCredentials: boolean;
  listeners: Record<string, (() => void)[]>;
  onmessage: (() => void) | null;
  addEventListener: (event: string, cb: () => void) => void;
  close: ReturnType<typeof vi.fn>;
}

let latestEventSource: MockEventSourceInstance | null = null;

class MockEventSource implements MockEventSourceInstance {
  url: string;
  withCredentials: boolean;
  listeners: Record<string, (() => void)[]> = {};
  onmessage: (() => void) | null = null;
  close = vi.fn();

  constructor(url: string, opts?: { withCredentials?: boolean }) {
    this.url = url;
    this.withCredentials = opts?.withCredentials ?? false;
    latestEventSource = this;
  }

  addEventListener(event: string, cb: () => void) {
    if (!this.listeners[event]) this.listeners[event] = [];
    this.listeners[event].push(cb);
  }
}

// ---------------------------------------------------------------------------
// Mock react-query
// ---------------------------------------------------------------------------

const mockInvalidateQueries = vi.fn();

vi.mock("@tanstack/react-query", () => ({
  useQueryClient: () => ({
    invalidateQueries: mockInvalidateQueries,
  }),
}));

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("useEventSource", () => {
  beforeEach(() => {
    latestEventSource = null;
    mockInvalidateQueries.mockClear();
    vi.stubGlobal("EventSource", MockEventSource);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("creates EventSource when enabled", () => {
    renderHook(() =>
      useEventSource("/api/v1/sse/stream", true, [["videos"]]),
    );

    expect(latestEventSource).not.toBeNull();
    expect(latestEventSource!.url).toBe("/api/v1/sse/stream");
    expect(latestEventSource!.withCredentials).toBe(true);
  });

  it("does not create EventSource when disabled", () => {
    renderHook(() =>
      useEventSource("/api/v1/sse/stream", false, [["videos"]]),
    );

    expect(latestEventSource).toBeNull();
  });

  it("closes EventSource on cleanup", () => {
    const { unmount } = renderHook(() =>
      useEventSource("/api/v1/sse/stream", true, [["videos"]]),
    );

    const es = latestEventSource!;
    expect(es.close).not.toHaveBeenCalled();

    unmount();

    expect(es.close).toHaveBeenCalledOnce();
  });

  it("registers event listeners for video_progress and batch_progress", () => {
    renderHook(() =>
      useEventSource("/api/v1/sse/stream", true, [["videos"]]),
    );

    const es = latestEventSource!;
    expect(es.listeners["video_progress"]).toHaveLength(1);
    expect(es.listeners["batch_progress"]).toHaveLength(1);
    expect(es.onmessage).not.toBeNull();
  });

  it("closes old EventSource and creates new one when url changes", () => {
    const { rerender } = renderHook(
      ({ url }) => useEventSource(url, true, [["videos"]]),
      { initialProps: { url: "/api/v1/sse/stream-1" } },
    );

    const firstEs = latestEventSource!;

    rerender({ url: "/api/v1/sse/stream-2" });

    expect(firstEs.close).toHaveBeenCalledOnce();
    expect(latestEventSource!.url).toBe("/api/v1/sse/stream-2");
  });
});
