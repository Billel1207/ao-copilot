import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { analysisApi, companyApi } from "@/lib/api";

export function useSummary(projectId: string, enabled = true) {
  return useQuery({
    queryKey: ["summary", projectId],
    queryFn: () => analysisApi.summary(projectId).then((r) => r.data),
    enabled: !!projectId && enabled,
    retry: false,
  });
}

export function useChecklist(
  projectId: string,
  filters: { criticality?: string; status?: string; category?: string } = {}
) {
  return useQuery({
    queryKey: ["checklist", projectId, filters],
    queryFn: () => analysisApi.checklist(projectId, filters).then((r) => r.data),
    enabled: !!projectId,
    retry: false,
  });
}

export function useCriteria(projectId: string) {
  return useQuery({
    queryKey: ["criteria", projectId],
    queryFn: () => analysisApi.criteria(projectId).then((r) => r.data),
    enabled: !!projectId,
    retry: false,
  });
}

export function useTriggerAnalysis(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => analysisApi.trigger(projectId).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["project", projectId] });
    },
  });
}

export function useGoNoGo(projectId: string, enabled = true) {
  return useQuery({
    queryKey: ["gonogo", projectId],
    queryFn: () => analysisApi.gonogo(projectId).then((r) => r.data),
    enabled: !!projectId && enabled,
    retry: false,
  });
}

export function useTimeline(projectId: string, enabled = true) {
  return useQuery({
    queryKey: ["timeline", projectId],
    queryFn: () => analysisApi.timeline(projectId).then((r) => r.data),
    enabled: !!projectId && enabled,
    retry: false,
  });
}

export function useUpdateTimelineTask(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ taskIndex, done }: { taskIndex: number; done: boolean }) =>
      analysisApi.updateTimelineTask(projectId, taskIndex, done).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["timeline", projectId] });
    },
  });
}

export function useUpdateChecklistItem(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ itemId, data }: { itemId: string; data: { status?: string; notes?: string } }) =>
      analysisApi.updateChecklistItem(projectId, itemId, data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["checklist", projectId] });
    },
  });
}

export function useGenerateText(projectId: string) {
  return useMutation({
    mutationFn: (itemId: string) =>
      analysisApi.generateText(projectId, itemId).then((r) => r.data),
  });
}

export function useChatDCE(projectId: string) {
  return useMutation({
    mutationFn: (question: string) =>
      analysisApi.chat(projectId, question).then((r) => r.data),
  });
}

export function useCcapRisks(projectId: string, enabled = true) {
  return useQuery({
    queryKey: ["ccap-risks", projectId],
    queryFn: () => analysisApi.ccapRisks(projectId).then((r) => r.data),
    enabled: !!projectId && enabled,
    retry: false,
  });
}

export function useDeadlines(projectId: string, enabled = true) {
  return useQuery({
    queryKey: ["deadlines", projectId],
    queryFn: () => analysisApi.deadlines(projectId).then((r) => r.data),
    enabled: !!projectId && enabled,
    retry: false,
  });
}

// ── Sprint V+W — Nouvelles analyses ────────────────────────────────

export function useRcAnalysis(projectId: string, enabled = true) {
  return useQuery({
    queryKey: ["rc-analysis", projectId],
    queryFn: () => analysisApi.rcAnalysis(projectId).then((r) => r.data),
    enabled: !!projectId && enabled,
    retry: false,
  });
}

export function useAeAnalysis(projectId: string, enabled = true) {
  return useQuery({
    queryKey: ["ae-analysis", projectId],
    queryFn: () => analysisApi.aeAnalysis(projectId).then((r) => r.data),
    enabled: !!projectId && enabled,
    retry: false,
  });
}

export function useDcCheck(projectId: string, enabled = true) {
  return useQuery({
    queryKey: ["dc-check", projectId],
    queryFn: () => analysisApi.dcCheck(projectId).then((r) => r.data),
    enabled: !!projectId && enabled,
    retry: false,
  });
}

export function useConflicts(projectId: string, enabled = true) {
  return useQuery({
    queryKey: ["conflicts", projectId],
    queryFn: () => analysisApi.conflicts(projectId).then((r) => r.data),
    enabled: !!projectId && enabled,
    retry: false,
  });
}

export function useQuestions(projectId: string, enabled = true) {
  return useQuery({
    queryKey: ["questions", projectId],
    queryFn: () => analysisApi.questions(projectId).then((r) => r.data),
    enabled: !!projectId && enabled,
    retry: false,
  });
}

export function useScoringSimulation(projectId: string, enabled = true) {
  return useQuery({
    queryKey: ["scoring-simulation", projectId],
    queryFn: () => analysisApi.scoringSimulation(projectId).then((r) => r.data),
    enabled: !!projectId && enabled,
    retry: false,
  });
}

export function useDpgfPricing(projectId: string, enabled = true) {
  return useQuery({
    queryKey: ["dpgf-pricing", projectId],
    queryFn: () => analysisApi.dpgfPricing(projectId).then((r) => r.data),
    enabled: !!projectId && enabled,
    retry: false,
  });
}

export function useCompanyProfile() {
  return useQuery({
    queryKey: ["company-profile"],
    queryFn: () => companyApi.getProfile().then((r) => r.data),
    retry: false,
  });
}

export function useUpdateCompanyProfile() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: object) => companyApi.updateProfile(data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["company-profile"] });
    },
  });
}
