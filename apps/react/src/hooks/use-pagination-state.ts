import { useState } from "react";

export function usePaginationState(defaultPageSize = 20) {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(defaultPageSize);

  const handlePageSizeChange = (size: number) => {
    setPageSize(size);
    setPage(1);
  };

  return {
    page,
    pageSize,
    setPage,
    setPageSize: handlePageSizeChange,
    paginationProps: {
      page,
      totalPages: 1,
      total: 0,
      pageSize,
      onPageChange: setPage,
      onPageSizeChange: handlePageSizeChange,
    },
  };
}
