import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { documentsApi } from "@/lib/api";

export function useDocuments(projectId: string) {
  return useQuery({
    queryKey: ["documents", projectId],
    queryFn: () => documentsApi.list(projectId).then((r) => r.data),
    enabled: !!projectId,
  });
}

export function useUploadDocument(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => documentsApi.upload(projectId, file).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["documents", projectId] });
      qc.invalidateQueries({ queryKey: ["project", projectId] });
    },
  });
}

export function useDeleteDocument(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (docId: string) => documentsApi.delete(projectId, docId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["documents", projectId] }),
  });
}
