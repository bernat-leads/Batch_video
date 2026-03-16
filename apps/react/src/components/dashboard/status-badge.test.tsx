import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { StatusBadge } from "./status-badge";

describe("StatusBadge", () => {
  it("renders the correct label for each known status", () => {
    const cases = [
      { status: "queued", expected: "Queued" },
      { status: "finished", expected: "Finished" },
      { status: "completed", expected: "Completed" },
      { status: "failed", expected: "Failed" },
      { status: "partially_completed", expected: "Partially Completed" },
    ];

    for (const { status, expected } of cases) {
      const { unmount } = render(<StatusBadge status={status} />);
      expect(screen.getByText(expected)).toBeInTheDocument();
      unmount();
    }
  });

  it("shows pipeline stage label when status is processing and stage is provided", () => {
    render(<StatusBadge status="processing" stage="tts" />);
    expect(screen.getByText("Generating Audio")).toBeInTheDocument();
  });

  it("shows stage-specific labels for all pipeline stages", () => {
    const stages = [
      { stage: "segmentation", expected: "Segmenting" },
      { stage: "image_generation", expected: "Generating Images" },
      { stage: "assembly", expected: "Assembling Video" },
    ];

    for (const { stage, expected } of stages) {
      const { unmount } = render(<StatusBadge status="processing" stage={stage} />);
      expect(screen.getByText(expected)).toBeInTheDocument();
      unmount();
    }
  });

  it("falls back to 'Processing' when status is processing but no stage", () => {
    render(<StatusBadge status="processing" />);
    expect(screen.getByText("Processing")).toBeInTheDocument();
  });

  it("falls back to 'Processing' for unknown status", () => {
    render(<StatusBadge status="unknown_status_xyz" />);
    expect(screen.getByText("Processing")).toBeInTheDocument();
  });

  it("applies animate-pulse class only when processing", () => {
    const { container, unmount } = render(<StatusBadge status="processing" />);
    const dot = container.querySelector(".animate-pulse");
    expect(dot).toBeInTheDocument();
    unmount();

    const { container: c2 } = render(<StatusBadge status="finished" />);
    expect(c2.querySelector(".animate-pulse")).not.toBeInTheDocument();
  });
});
