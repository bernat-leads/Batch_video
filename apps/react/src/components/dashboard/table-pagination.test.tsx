import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { TablePagination } from "./table-pagination";

describe("TablePagination", () => {
  it("returns null when single page and no page size changer", () => {
    const { container } = render(
      <TablePagination
        page={1}
        totalPages={1}
        total={5}
        pageSize={20}
        onPageChange={vi.fn()}
      />,
    );
    expect(container.firstChild).toBeNull();
  });

  it("renders page size selector even on single page when onPageSizeChange provided", () => {
    render(
      <TablePagination
        page={1}
        totalPages={1}
        total={5}
        pageSize={20}
        onPageChange={vi.fn()}
        onPageSizeChange={vi.fn()}
      />,
    );
    expect(screen.getByText("1–5 of 5")).toBeInTheDocument();
  });

  it("shows correct range text", () => {
    render(
      <TablePagination
        page={2}
        totalPages={3}
        total={55}
        pageSize={20}
        onPageChange={vi.fn()}
      />,
    );
    expect(screen.getByText("21–40 of 55")).toBeInTheDocument();
  });

  it("shows 0 results when total is 0", () => {
    render(
      <TablePagination
        page={1}
        totalPages={0}
        total={0}
        pageSize={20}
        onPageChange={vi.fn()}
        onPageSizeChange={vi.fn()}
      />,
    );
    expect(screen.getByText("0 results")).toBeInTheDocument();
  });

  it("disables prev button on first page", () => {
    render(
      <TablePagination
        page={1}
        totalPages={5}
        total={100}
        pageSize={20}
        onPageChange={vi.fn()}
      />,
    );
    const buttons = screen.getAllByRole("button");
    // First button is prev
    expect(buttons[0]).toBeDisabled();
  });

  it("disables next button on last page", () => {
    render(
      <TablePagination
        page={5}
        totalPages={5}
        total={100}
        pageSize={20}
        onPageChange={vi.fn()}
      />,
    );
    const buttons = screen.getAllByRole("button");
    // Last button is next
    expect(buttons[buttons.length - 1]).toBeDisabled();
  });

  it("calls onPageChange when clicking a page number", async () => {
    const user = userEvent.setup();
    const onPageChange = vi.fn();

    render(
      <TablePagination
        page={1}
        totalPages={5}
        total={100}
        pageSize={20}
        onPageChange={onPageChange}
      />,
    );

    await user.click(screen.getByRole("button", { name: "3" }));
    expect(onPageChange).toHaveBeenCalledWith(3);
  });

  it("calls onPageChange with page-1 when clicking prev", async () => {
    const user = userEvent.setup();
    const onPageChange = vi.fn();

    render(
      <TablePagination
        page={3}
        totalPages={5}
        total={100}
        pageSize={20}
        onPageChange={onPageChange}
      />,
    );

    const buttons = screen.getAllByRole("button");
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion -- test assertion, buttons[0] always exists
    await user.click(buttons[0]!); // prev button
    expect(onPageChange).toHaveBeenCalledWith(2);
  });

  it("calls onPageSizeChange when selecting a different page size", async () => {
    const user = userEvent.setup();
    const onPageSizeChange = vi.fn();

    render(
      <TablePagination
        page={1}
        totalPages={5}
        total={100}
        pageSize={20}
        onPageChange={vi.fn()}
        onPageSizeChange={onPageSizeChange}
      />,
    );

    await user.selectOptions(screen.getByRole("combobox"), "50");
    expect(onPageSizeChange).toHaveBeenCalledWith(50);
  });

  it("shows ellipsis for many pages when current is in the middle", () => {
    render(
      <TablePagination
        page={5}
        totalPages={10}
        total={200}
        pageSize={20}
        onPageChange={vi.fn()}
      />,
    );
    // Should show: 1 ... 4 5 6 ... 10
    expect(screen.getByRole("button", { name: "1" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "4" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "5" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "6" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "10" })).toBeInTheDocument();
    // Two ellipses
    const ellipses = screen.getAllByText("...");
    expect(ellipses).toHaveLength(2);
  });
});
