/**
 * Shared TypeScript interfaces used across multiple components.
 * Keep domain-specific types in their respective modules.
 */

/** Pagination state and callbacks shared by all paginated table views. */
export interface PaginationInfo {
  page: number;
  totalPages: number;
  total: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onPageSizeChange?: (pageSize: number) => void;
}
