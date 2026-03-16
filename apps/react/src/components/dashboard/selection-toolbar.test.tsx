import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { SelectionToolbar } from "./selection-toolbar";

describe("SelectionToolbar", () => {
  it("displays the selected count", () => {
    render(
      <SelectionToolbar count={3} onExport={vi.fn()} />,
    );
    expect(screen.getByText("3 selected")).toBeInTheDocument();
  });

  it("calls onExport when export button is clicked", async () => {
    const user = userEvent.setup();
    const onExport = vi.fn();

    render(
      <SelectionToolbar count={1} onExport={onExport} />,
    );

    await user.click(screen.getByText("Export"));
    expect(onExport).toHaveBeenCalledOnce();
  });

  it("uses custom export label when provided", () => {
    render(
      <SelectionToolbar
        count={2}
        onExport={vi.fn()}
        exportLabel="Export Selected Videos"
      />,
    );
    expect(screen.getByText("Export Selected Videos")).toBeInTheDocument();
  });

  it("hides delete button when onDelete is not provided", () => {
    render(
      <SelectionToolbar count={1} onExport={vi.fn()} />,
    );
    expect(screen.queryByText("Delete")).not.toBeInTheDocument();
  });

  it("shows delete button when onDelete is provided", () => {
    render(
      <SelectionToolbar count={1} onExport={vi.fn()} onDelete={vi.fn()} />,
    );
    expect(screen.getByText("Delete")).toBeInTheDocument();
  });

  it("opens confirmation dialog on delete click and calls onDelete on confirm", async () => {
    const user = userEvent.setup();
    const onDelete = vi.fn();

    render(
      <SelectionToolbar count={3} onExport={vi.fn()} onDelete={onDelete} />,
    );

    // Click the delete trigger button
    await user.click(screen.getByText("Delete"));

    // Confirmation dialog should appear with pluralized title
    expect(screen.getByText("Delete 3 batches?")).toBeInTheDocument();

    // Confirm deletion
    const confirmButton = screen.getByRole("button", { name: "Delete" });
    // There are two "Delete" buttons — the trigger and the confirm. Click the dialog one.
    const allDeletes = screen.getAllByText("Delete");
    const dialogConfirm = allDeletes.find((el) =>
      el.closest("[role='alertdialog']"),
    );
    if (dialogConfirm) await user.click(dialogConfirm);
    expect(onDelete).toHaveBeenCalledOnce();
  });

  it("uses singular 'batch' for count of 1", async () => {
    const user = userEvent.setup();

    render(
      <SelectionToolbar count={1} onExport={vi.fn()} onDelete={vi.fn()} />,
    );

    await user.click(screen.getByText("Delete"));
    expect(screen.getByText("Delete 1 batch?")).toBeInTheDocument();
  });
});
