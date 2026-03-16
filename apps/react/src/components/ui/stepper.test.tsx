import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Stepper } from "./stepper";

const STEPS = [
  { key: "upload", label: "Upload" },
  { key: "map", label: "Map Columns" },
  { key: "review", label: "Review" },
];

describe("Stepper", () => {
  it("renders all step labels", () => {
    render(<Stepper steps={STEPS} current="upload" />);
    expect(screen.getByText("Upload")).toBeInTheDocument();
    expect(screen.getByText("Map Columns")).toBeInTheDocument();
    expect(screen.getByText("Review")).toBeInTheDocument();
  });

  it("shows step numbers for current and upcoming steps", () => {
    render(<Stepper steps={STEPS} current="map" />);
    // Step 2 (map) is current — shows "2"
    expect(screen.getByText("2")).toBeInTheDocument();
    // Step 3 (review) is upcoming — shows "3"
    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("shows check icon for completed steps instead of number", () => {
    const { container } = render(<Stepper steps={STEPS} current="review" />);
    // Steps 1 and 2 are completed — should not show "1" or "2" text
    expect(screen.queryByText("1")).not.toBeInTheDocument();
    expect(screen.queryByText("2")).not.toBeInTheDocument();
    // Check icons should be rendered (lucide Check renders an svg)
    const svgs = container.querySelectorAll("svg");
    expect(svgs.length).toBeGreaterThanOrEqual(2);
  });

  it("applies brand styling to current step label", () => {
    render(<Stepper steps={STEPS} current="map" />);
    const label = screen.getByText("Map Columns");
    expect(label).toHaveClass("text-brand");
  });

  it("applies muted styling to upcoming step labels", () => {
    render(<Stepper steps={STEPS} current="upload" />);
    expect(screen.getByText("Map Columns")).toHaveClass("text-text-muted");
    expect(screen.getByText("Review")).toHaveClass("text-text-muted");
  });

  it("applies primary styling to completed step labels", () => {
    render(<Stepper steps={STEPS} current="review" />);
    expect(screen.getByText("Upload")).toHaveClass("text-text-primary");
    expect(screen.getByText("Map Columns")).toHaveClass("text-text-primary");
  });
});
