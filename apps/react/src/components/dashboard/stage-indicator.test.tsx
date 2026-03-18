import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { StageIndicator } from "./stage-indicator";

describe("StageIndicator", () => {
  describe("compact variant", () => {
    it("renders 7 stage bars", () => {
      const { container } = render(
        <StageIndicator currentStage="tts" status="processing" variant="compact" />,
      );
      const bars = container.querySelectorAll("[title]");
      expect(bars).toHaveLength(7);
    });

    it("colors past stages with success", () => {
      const { container } = render(
        <StageIndicator currentStage="image_generation" status="processing" variant="compact" />,
      );
      const bars = container.querySelectorAll("[title]");
      // queued (0), tts (1), segmentation (2) should be past (success)
      expect(bars[0]).toHaveClass("bg-status-success");
      expect(bars[1]).toHaveClass("bg-status-success");
      expect(bars[2]).toHaveClass("bg-status-success");
      // image_generation (3) is current
      expect(bars[3]).toHaveClass("bg-brand");
      // assembly (4), upload (5), done (6) are future
      expect(bars[4]).toHaveClass("bg-border");
      expect(bars[5]).toHaveClass("bg-border");
      expect(bars[6]).toHaveClass("bg-border");
    });

    it("colors current stage as error when status is failed", () => {
      const { container } = render(
        <StageIndicator currentStage="segmentation" status="failed" variant="compact" />,
      );
      const bars = container.querySelectorAll("[title]");
      // segmentation (2) is current and failed
      expect(bars[2]).toHaveClass("bg-status-error");
    });

    it("colors all stages success when status is finished", () => {
      const { container } = render(
        <StageIndicator currentStage="done" status="finished" variant="compact" />,
      );
      const bars = container.querySelectorAll("[title]");
      for (const bar of bars) {
        expect(bar).toHaveClass("bg-status-success");
      }
    });
  });

  describe("full variant", () => {
    it("renders all stage labels with icons", () => {
      render(
        <StageIndicator currentStage="tts" status="processing" variant="full" />,
      );
      expect(screen.getByText("Queued")).toBeInTheDocument();
      expect(screen.getByText("Audio (TTS)")).toBeInTheDocument();
      expect(screen.getByText("Segmentation")).toBeInTheDocument();
      expect(screen.getByText("Image Gen")).toBeInTheDocument();
      expect(screen.getByText("Assembly")).toBeInTheDocument();
      expect(screen.getByText("Upload")).toBeInTheDocument();
      expect(screen.getByText("Done")).toBeInTheDocument();
    });

    it("applies success styling to past stages", () => {
      render(
        <StageIndicator currentStage="segmentation" status="processing" variant="full" />,
      );
      // "Queued" parent div should have success-light styling
      const queued = screen.getByText("Queued").closest("div[class*='rounded-lg']");
      expect(queued).toHaveClass("bg-status-success-light");
    });

    it("applies brand styling to active stage", () => {
      render(
        <StageIndicator currentStage="segmentation" status="processing" variant="full" />,
      );
      const seg = screen.getByText("Segmentation").closest("div[class*='rounded-lg']");
      expect(seg).toHaveClass("text-brand");
    });

    it("applies error styling when failed at current stage", () => {
      render(
        <StageIndicator currentStage="image_generation" status="failed" variant="full" />,
      );
      const imgGen = screen.getByText("Image Gen").closest("div[class*='rounded-lg']");
      expect(imgGen).toHaveClass("bg-status-error-light");
    });
  });
});
