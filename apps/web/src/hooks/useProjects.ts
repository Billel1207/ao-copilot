import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { projectsApi } from "@/lib/api";

export function useProjects(params?: { skip?: number; limit?: number; status?: string; q?: string }) {
  return useQuery({
    queryKey: ["projects", params],
    queryFn: () => projectsApi.list(params).then((r) => r.data),
  });
}

export function useProject(id: string) {
  return useQuery({
    queryKey: ["project", id],
    queryFn: () => projectsApi.get(id).then((r) => r.data),
    enabled: !!id,
    refetchInterval: (query) => {
      const data = query.state.data;
      return data?.status === "analyzing" ? 3000 : false;
    },
  });
}

export function useCreateProject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: object) => projectsApi.create(data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["projects"] }),
  });
}
