import { describe, it, expect } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { usePaginationState } from "./use-pagination-state";

describe("usePaginationState", () => {
  it("returns default state (page=1, pageSize=20)", () => {
    const { result } = renderHook(() => usePaginationState());

    expect(result.current.page).toBe(1);
    expect(result.current.pageSize).toBe(20);
  });

  it("accepts a custom default page size", () => {
    const { result } = renderHook(() => usePaginationState(50));

    expect(result.current.page).toBe(1);
    expect(result.current.pageSize).toBe(50);
  });

  it("setPage updates the current page", () => {
    const { result } = renderHook(() => usePaginationState());

    act(() => {
      result.current.setPage(3);
    });

    expect(result.current.page).toBe(3);
  });

  it("setPageSize resets page to 1", () => {
    const { result } = renderHook(() => usePaginationState());

    // First navigate to page 3
    act(() => {
      result.current.setPage(3);
    });
    expect(result.current.page).toBe(3);

    // Changing page size should reset page to 1
    act(() => {
      result.current.setPageSize(50);
    });

    expect(result.current.pageSize).toBe(50);
    expect(result.current.page).toBe(1);
  });

  it("paginationProps contains correct callbacks", () => {
    const { result } = renderHook(() => usePaginationState());

    const { paginationProps } = result.current;

    expect(paginationProps.page).toBe(1);
    expect(paginationProps.pageSize).toBe(20);
    expect(paginationProps.totalPages).toBe(1);
    expect(paginationProps.total).toBe(0);
    expect(typeof paginationProps.onPageChange).toBe("function");
    expect(typeof paginationProps.onPageSizeChange).toBe("function");
  });

  it("paginationProps.onPageChange updates the page", () => {
    const { result } = renderHook(() => usePaginationState());

    act(() => {
      result.current.paginationProps.onPageChange(5);
    });

    expect(result.current.page).toBe(5);
    expect(result.current.paginationProps.page).toBe(5);
  });

  it("paginationProps.onPageSizeChange resets page to 1", () => {
    const { result } = renderHook(() => usePaginationState());

    act(() => {
      result.current.setPage(4);
    });
    expect(result.current.page).toBe(4);

    act(() => {
      result.current.paginationProps.onPageSizeChange(100);
    });

    expect(result.current.pageSize).toBe(100);
    expect(result.current.page).toBe(1);
  });
});
