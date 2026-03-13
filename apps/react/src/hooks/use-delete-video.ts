import { useQueryClient } from "@tanstack/react-query";
import {
  useDeleteVideoApiV1VideosVideoIdDelete,
  getListVideosApiV1VideosGetQueryKey,
  getListBatchesApiV1BatchesGetQueryKey,
} from "@packages/api-client";
import { toast } from "sonner";

export function useDeleteVideo(options?: { onSuccess?: () => void }) {
  const queryClient = useQueryClient();
  return useDeleteVideoApiV1VideosVideoIdDelete({
    mutation: {
      onSuccess: () => {
        queryClient.invalidateQueries({
          queryKey: getListVideosApiV1VideosGetQueryKey(),
        });
        queryClient.invalidateQueries({
          queryKey: getListBatchesApiV1BatchesGetQueryKey(),
        });
        toast.success("Video deleted");
        options?.onSuccess?.();
      },
      onError: () => {
        toast.error("Failed to delete video");
      },
    },
  });
}
