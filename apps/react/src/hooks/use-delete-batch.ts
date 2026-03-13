import { useQueryClient } from "@tanstack/react-query";
import {
  useDeleteBatchApiV1BatchesBatchIdDelete,
  getListBatchesApiV1BatchesGetQueryKey,
} from "@packages/api-client";
import { toast } from "sonner";

export function useDeleteBatch(options?: { onSuccess?: () => void }) {
  const queryClient = useQueryClient();
  return useDeleteBatchApiV1BatchesBatchIdDelete({
    mutation: {
      onSuccess: () => {
        queryClient.invalidateQueries({
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
