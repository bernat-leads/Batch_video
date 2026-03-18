import { describe, it, expect } from "vitest";
import {
  formatDuration,
  formatDate,
  formatCurrency,
  formatSeconds,
  formatFileSize,
  formatKenBurns,
} from "./format";

describe("formatDuration", () => {
  it("returns 0s for zero milliseconds", () => {
    expect(formatDuration(0)).toBe("0s");
  });

  it("returns seconds only when under a minute", () => {
    expect(formatDuration(45_000)).toBe("45s");
  });

  it("returns minutes and seconds", () => {
    expect(formatDuration(150_000)).toBe("2m 30s");
  });

  it("returns exact minutes with 0s remainder", () => {
    expect(formatDuration(120_000)).toBe("2m 0s");
  });

  it("floors fractional milliseconds", () => {
    expect(formatDuration(1_999)).toBe("1s");
  });

  it("handles large values", () => {
    expect(formatDuration(3_661_000)).toBe("61m 1s");
  });
});

describe("formatDate", () => {
  it("formats ISO string with month, day, and time", () => {
    const result = formatDate("2026-03-15T14:30:00Z");
    // Locale-dependent — just verify it contains the month and has content
    expect(result).toContain("Mar");
    expect(result).toContain("15");
  });
});

describe("formatCurrency", () => {
  it("formats zero", () => {
    expect(formatCurrency(0)).toBe("$0.00");
  });

  it("formats positive values with two decimals", () => {
    expect(formatCurrency(1.5)).toBe("$1.50");
  });

  it("rounds to two decimal places", () => {
    expect(formatCurrency(1.999)).toBe("$2.00");
  });

  it("handles negative values", () => {
    expect(formatCurrency(-3.5)).toBe("$-3.50");
  });
});

describe("formatSeconds", () => {
  it("formats zero seconds", () => {
    expect(formatSeconds(0)).toBe("0:00");
  });

  it("pads single-digit seconds", () => {
    expect(formatSeconds(5)).toBe("0:05");
  });

  it("formats minutes and seconds", () => {
    expect(formatSeconds(125)).toBe("2:05");
  });

  it("floors fractional seconds", () => {
    expect(formatSeconds(90.7)).toBe("1:30");
  });
});

describe("formatFileSize", () => {
  it("returns em-dash for zero bytes", () => {
    expect(formatFileSize(0)).toBe("\u2014");
  });

  it("formats kilobytes", () => {
    expect(formatFileSize(512 * 1024)).toBe("512 KB");
  });

  it("formats megabytes with one decimal", () => {
    expect(formatFileSize(2.5 * 1024 * 1024)).toBe("2.5 MB");
  });

  it("uses MB for exactly 1 MB", () => {
    expect(formatFileSize(1024 * 1024)).toBe("1.0 MB");
  });

  it("uses KB for just under 1 MB", () => {
    const result = formatFileSize(1024 * 1024 - 1);
    expect(result).toContain("KB");
  });
});

describe("formatKenBurns", () => {
  it("returns em-dash for null", () => {
    expect(formatKenBurns(null)).toBe("\u2014");
  });

  it("returns em-dash for undefined", () => {
    expect(formatKenBurns(undefined)).toBe("\u2014");
  });

  it("returns em-dash for empty config", () => {
    expect(formatKenBurns({})).toBe("\u2014");
  });

  it("formats direction and scale", () => {
    expect(formatKenBurns({ direction: "zoom_in", scale: 1.5 })).toBe("zoom in 1.5x");
  });

  it("formats direction only", () => {
    expect(formatKenBurns({ direction: "pan_left" })).toBe("pan left");
  });

  it("formats scale only", () => {
    expect(formatKenBurns({ scale: 2 })).toBe("2x");
  });
});
