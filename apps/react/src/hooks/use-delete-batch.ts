import { useQueryClient } from "@tanstack/react-query";
import {
  useDeleteBatchApiV1BatchesBatchIdDelete,
  getListBatchesApiV1BatchesGetQueryKey,
} from "@packages/api-client";
import { toast } from "sonner";

/**
 * Mutation hook for deleting a batch. Invalidates the batch list
 * cache on success and shows toast notifications.
 */
export function useDeleteBatch(options?: { onSuccess?: () => void }) {
  const queryClient = useQueryClient();
  return useDeleteBatchApiV1BatchesBatchIdDelete({
    mutation: {
      onSuccess: () => {
        void queryClient.invalidateQueries({
          queryKey: getListBatchesApiV1BatchesGetQueryKey(),
        });
        toast.success("Batch deleted");
        options?.onSuccess?.();
      },
      onError: () => {
        toast.error("Failed to delete batch");
      },
    },
  });
}
