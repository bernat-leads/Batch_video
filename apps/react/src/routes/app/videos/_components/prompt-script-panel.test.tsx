import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { PromptScriptPanel } from "./prompt-script-panel";

describe("PromptScriptPanel", () => {
  it("returns null when both prompt and scriptText are empty", () => {
    const { container } = render(
      <PromptScriptPanel prompt={null} scriptText="" />,
    );
    expect(container.firstChild).toBeNull();
  });

  it("renders toggle button when scriptText is provided", () => {
    render(<PromptScriptPanel scriptText="Hello world" />);
    expect(screen.getByText("Show Prompt & Script")).toBeInTheDocument();
  });

  it("starts collapsed — content not visible", () => {
    render(<PromptScriptPanel prompt="Generate..." scriptText="Script..." />);
    expect(screen.queryByText("Generate...")).not.toBeInTheDocument();
    expect(screen.queryByText("Script...")).not.toBeInTheDocument();
  });

  it("expands on click and shows both prompt and script", async () => {
    const user = userEvent.setup();

    render(
      <PromptScriptPanel prompt="Generate branded content" scriptText="Buy now!" />,
    );

    await user.click(screen.getByText("Show Prompt & Script"));

    expect(screen.getByText("Hide Prompt & Script")).toBeInTheDocument();
    expect(screen.getByText("Generate branded content")).toBeInTheDocument();
    expect(screen.getByText("Buy now!")).toBeInTheDocument();
  });

  it("collapses on second click", async () => {
    const user = userEvent.setup();

    render(<PromptScriptPanel prompt="P" scriptText="S" />);

    await user.click(screen.getByText("Show Prompt & Script"));
    expect(screen.getByText("P")).toBeInTheDocument();

    await user.click(screen.getByText("Hide Prompt & Script"));
    expect(screen.queryByText("P")).not.toBeInTheDocument();
  });

  it("shows only script panel when prompt is null", async () => {
    const user = userEvent.setup();

    render(<PromptScriptPanel prompt={null} scriptText="Just a script" />);

    await user.click(screen.getByText("Show Prompt & Script"));

    expect(screen.getByText("Script")).toBeInTheDocument();
    expect(screen.getByText("Just a script")).toBeInTheDocument();
    expect(screen.queryByText("Prompt")).not.toBeInTheDocument();
  });

  it("shows only script panel when prompt is empty string", async () => {
    const user = userEvent.setup();

    render(<PromptScriptPanel prompt="" scriptText="Script only" />);

    await user.click(screen.getByText("Show Prompt & Script"));

    expect(screen.queryByText("Prompt")).not.toBeInTheDocument();
    expect(screen.getByText("Script only")).toBeInTheDocument();
  });
});
