"use client";
import { useState } from "react";
import {
  MessageSquare, HelpCircle, CheckCircle2, Flag, Trash2,
  ChevronDown, ChevronUp, Send, Loader2,
} from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { annotationsApi } from "@/lib/api";
import { useAuthStore } from "@/stores/auth";
import { cn } from "@/lib/utils";

// ── Types ─────────────────────────────────────────────────────────────────────

type AnnotationType = "comment" | "question" | "validated" | "flag";

interface Annotation {
  id: string;
  checklist_item_id: string;
  project_id: string;
  user_id: string;
  content: string;
  annotation_type: AnnotationType;
  author_name: string | null;
  author_email: string | null;
  created_at: string;
  updated_at: string;
}

interface Props {
  projectId: string;
  itemId: string;
}

// ── Annotation type config ────────────────────────────────────────────────────

const TYPE_CONFIG: Record<AnnotationType, { label: string; icon: React.ReactNode; badgeClass: string }> = {
  comment: {
    label: "Commentaire",
    icon: <MessageSquare className="w-3 h-3" />,
    badgeClass: "bg-slate-100 text-slate-600",
  },
  question: {
    label: "Question",
    icon: <HelpCircle className="w-3 h-3" />,
    badgeClass: "bg-amber-100 text-amber-700",
  },
  validated: {
    label: "Validé",
    icon: <CheckCircle2 className="w-3 h-3" />,
    badgeClass: "bg-emerald-100 text-emerald-700",
  },
  flag: {
    label: "Signalé",
    icon: <Flag className="w-3 h-3" />,
    badgeClass: "bg-rose-100 text-rose-700",
  },
};

// ── Helpers ───────────────────────────────────────────────────────────────────

function getInitials(name: string | null, email: string | null): string {
  if (name) {
    const parts = name.trim().split(" ");
    return parts.length >= 2
      ? `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase()
      : name.slice(0, 2).toUpperCase();
  }
  if (email) return email.slice(0, 2).toUpperCase();
  return "??";
}

function formatRelative(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return "à l'instant";
  if (minutes < 60) return `il y a ${minutes} min`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `il y a ${hours}h`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `il y a ${days}j`;
  return new Date(iso).toLocaleDateString("fr-FR", { day: "numeric", month: "short" });
}

// ── Avatar ────────────────────────────────────────────────────────────────────

function Avatar({ name, email }: { name: string | null; email: string | null }) {
  const initials = getInitials(name, email);
  const colors = [
    "bg-blue-100 text-blue-700",
    "bg-violet-100 text-violet-700",
    "bg-emerald-100 text-emerald-700",
    "bg-amber-100 text-amber-700",
    "bg-rose-100 text-rose-700",
  ];
  // Stable color based on email/name
  const key = (email ?? name ?? "").charCodeAt(0) % colors.length;
  return (
    <div className={`w-7 h-7 rounded-full flex items-center justify-center text-[10px] font-bold flex-shrink-0 ${colors[key]}`}>
      {initials}
    </div>
  );
}

// ── Single annotation row ─────────────────────────────────────────────────────

function AnnotationRow({
  annotation,
  projectId,
  itemId,
  canDelete,
}: {
  annotation: Annotation;
  projectId: string;
  itemId: string;
  canDelete: boolean;
}) {
  const queryClient = useQueryClient();
  const typeConfig = TYPE_CONFIG[annotation.annotation_type] ?? TYPE_CONFIG.comment;

  const deleteMutation = useMutation({
    mutationFn: () => annotationsApi.delete(projectId, itemId, annotation.id),
    onSuccess: () => {
      toast.success("Annotation supprimée");
      queryClient.invalidateQueries({ queryKey: ["annotations", projectId, itemId] });
    },
    onError: () => toast.error("Impossible de supprimer l'annotation"),
  });

  return (
    <div className="flex gap-2.5 group animate-fade-in">
      <Avatar name={annotation.author_name} email={annotation.author_email} />

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs font-semibold text-slate-700">
            {annotation.author_name ?? annotation.author_email ?? "Utilisateur"}
          </span>
          <span
            className={cn(
              "inline-flex items-center gap-1 text-[10px] font-semibold px-1.5 py-0.5 rounded-full",
              typeConfig.badgeClass
            )}
          >
            {typeConfig.icon}
            {typeConfig.label}
          </span>
          <span className="text-[10px] text-slate-400 ml-auto">
            {formatRelative(annotation.created_at)}
          </span>
          {canDelete && (
            <button
              onClick={() => deleteMutation.mutate()}
              disabled={deleteMutation.isPending}
              className="opacity-0 group-hover:opacity-100 transition-opacity p-0.5 rounded
                         text-slate-300 hover:text-rose-500 hover:bg-rose-50"
              title="Supprimer"
            >
              {deleteMutation.isPending ? (
                <Loader2 className="w-3 h-3 animate-spin" />
              ) : (
                <Trash2 className="w-3 h-3" />
              )}
            </button>
          )}
        </div>

        <p className="text-xs text-slate-600 mt-1 leading-relaxed whitespace-pre-wrap break-words">
          {annotation.content}
        </p>
      </div>
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────

export function AnnotationThread({ projectId, itemId }: Props) {
  const { user } = useAuthStore();
  const queryClient = useQueryClient();
  const [isOpen, setIsOpen] = useState(false);
  const [newContent, setNewContent] = useState("");
  const [newType, setNewType] = useState<AnnotationType>("comment");

  const isAdmin = user?.role === "admin" || user?.role === "owner";

  // Fetch annotations
  const { data: annotations = [], isLoading } = useQuery<Annotation[]>({
    queryKey: ["annotations", projectId, itemId],
    queryFn: () => annotationsApi.list(projectId, itemId),
    enabled: isOpen,
  });

  // Create annotation mutation
  const createMutation = useMutation({
    mutationFn: () =>
      annotationsApi.create(projectId, itemId, {
        content: newContent.trim(),
        annotation_type: newType,
      }),
    onSuccess: () => {
      setNewContent("");
      setNewType("comment");
      queryClient.invalidateQueries({ queryKey: ["annotations", projectId, itemId] });
    },
    onError: () => toast.error("Impossible d'ajouter l'annotation"),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newContent.trim()) return;
    createMutation.mutate();
  };

  return (
    <div className="mt-2">
      {/* Toggle */}
      <button
        type="button"
        onClick={() => setIsOpen(prev => !prev)}
        className="inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-primary-600 transition-colors"
      >
        <MessageSquare className="w-3.5 h-3.5" />
        Commentaires
        {annotations.length > 0 && (
          <span className="px-1.5 py-0.5 bg-slate-100 rounded-full text-[10px] font-bold text-slate-600">
            {annotations.length}
          </span>
        )}
        {isOpen ? (
          <ChevronUp className="w-3 h-3" />
        ) : (
          <ChevronDown className="w-3 h-3" />
        )}
      </button>

      {/* Thread panel */}
      {isOpen && (
        <div className="mt-2 space-y-3 animate-fade-in">
          {/* Existing annotations */}
          {isLoading ? (
            <div className="flex items-center gap-2 text-xs text-slate-400 py-2">
              <Loader2 className="w-3 h-3 animate-spin" />
              Chargement…
            </div>
          ) : annotations.length === 0 ? (
            <p className="text-xs text-slate-400 italic py-1">
              Aucun commentaire. Soyez le premier à commenter.
            </p>
          ) : (
            <div className="space-y-3 pl-1">
              {annotations.map(a => (
                <AnnotationRow
                  key={a.id}
                  annotation={a}
                  projectId={projectId}
                  itemId={itemId}
                  canDelete={isAdmin || a.user_id === user?.id}
                />
              ))}
            </div>
          )}

          {/* Add annotation form */}
          <form onSubmit={handleSubmit} className="flex flex-col gap-2 pt-1 border-t border-slate-100">
            <div className="flex gap-2 items-start">
              <Avatar name={user?.full_name ?? null} email={user?.email ?? null} />

              <div className="flex-1 space-y-2">
                <textarea
                  value={newContent}
                  onChange={e => setNewContent(e.target.value)}
                  placeholder="Ajouter un commentaire, une question…"
                  rows={2}
                  maxLength={2000}
                  className="w-full text-xs px-3 py-2 border border-slate-200 rounded-xl
                             focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent
                             transition-all resize-none placeholder:text-slate-400"
                />

                <div className="flex items-center gap-2 flex-wrap">
                  {/* Type selector */}
                  <div className="flex items-center gap-1">
                    {(Object.entries(TYPE_CONFIG) as [AnnotationType, typeof TYPE_CONFIG[AnnotationType]][]).map(
                      ([type, cfg]) => (
                        <button
                          key={type}
                          type="button"
                          onClick={() => setNewType(type)}
                          className={cn(
                            "inline-flex items-center gap-1 px-2 py-1 rounded-full text-[10px] font-semibold border transition-all",
                            newType === type
                              ? `${cfg.badgeClass} border-transparent shadow-sm`
                              : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
                          )}
                        >
                          {cfg.icon}
                          {cfg.label}
                        </button>
                      )
                    )}
                  </div>

                  <button
                    type="submit"
                    disabled={createMutation.isPending || !newContent.trim()}
                    className="ml-auto inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold
                               btn-primary-gradient disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {createMutation.isPending ? (
                      <Loader2 className="w-3 h-3 animate-spin" />
                    ) : (
                      <Send className="w-3 h-3" />
                    )}
                    Envoyer
                  </button>
                </div>
              </div>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
