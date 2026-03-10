import { useQuery } from "@tanstack/react-query";
import { knowledgeApi } from "@/lib/api";

interface GlossaryTerm {
  term: string;
  definition: string;
  category?: string;
}

export function useGlossary() {
  return useQuery<GlossaryTerm[]>({
    queryKey: ["glossary-terms"],
    queryFn: async () => {
      const res = await knowledgeApi.listGlossary();
      return res.data?.terms || res.data || [];
    },
    staleTime: 30 * 60 * 1000, // 30 min — glossaire change rarement
    retry: false,
  });
}
