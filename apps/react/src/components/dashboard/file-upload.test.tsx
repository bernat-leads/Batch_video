import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { FileUpload } from "./file-upload";

describe("FileUpload", () => {
  it("renders the drop zone with instructions", () => {
    render(<FileUpload onFileParsed={vi.fn()} />);
    expect(screen.getByText("Drop your Excel or CSV file here")).toBeInTheDocument();
    expect(screen.getByText(/click to browse/)).toBeInTheDocument();
  });

  it("shows error for unsupported file type via drop", async () => {
    render(<FileUpload onFileParsed={vi.fn()} />);

    const dropZone = screen.getByRole("button");
    const badFile = new File(["data"], "photo.png", { type: "image/png" });

    fireEvent.drop(dropZone, {
      dataTransfer: { files: [badFile] },
    });

    await waitFor(() => {
      expect(screen.getByText(/Please upload an Excel/)).toBeInTheDocument();
    });
  });

  it("does not show file type error for .csv extension", async () => {
    render(<FileUpload onFileParsed={vi.fn()} />);

    const dropZone = screen.getByRole("button");
    // .csv extension with empty MIME — should pass the extension check
    const csvFile = new File(["col1,col2\nval1,val2"], "data.csv", { type: "" });

    fireEvent.drop(dropZone, {
      dataTransfer: { files: [csvFile] },
    });

    // Should NOT show the file type error (may show a parse error instead)
    await waitFor(() => {
      expect(screen.queryByText(/Please upload an Excel/)).not.toBeInTheDocument();
    });
  });

  it("accepts dragOver and shows drag state", () => {
    render(<FileUpload onFileParsed={vi.fn()} />);

    const dropZone = screen.getByRole("button");

    fireEvent.dragOver(dropZone, { dataTransfer: { files: [] } });
    // Should apply dragging border class
    expect(dropZone).toHaveClass("border-brand");

    fireEvent.dragLeave(dropZone);
    expect(dropZone).not.toHaveClass("border-brand");
  });
});
