"use client";

export const dynamic = "force-dynamic";
import { useState, useMemo } from "react";
import {
  BookOpen, Plus, Search, Copy, Check, Pencil, Trash2,
  Loader2, X, Tag, ChevronDown, BookMarked,
} from "lucide-react";
import { toast } from "sonner";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { libraryApi } from "@/lib/api";

// ── Types ─────────────────────────────────────────────────────────────────────

interface Snippet {
  id: string;
  org_id: string;
  title: string;
  content: string;
  tags: string[];
  category: string | null;
  usage_count: number;
  last_used_at: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
}

type Category = "methodo" | "references" | "equipe" | "moyens" | "qualite";

const CATEGORIES: { value: Category; label: string; color: string }[] = [
  { value: "methodo",    label: "Méthodologie",   color: "bg-blue-100 text-blue-800" },
  { value: "references", label: "Références",      color: "bg-violet-100 text-violet-800" },
  { value: "equipe",     label: "Équipe",          color: "bg-emerald-100 text-emerald-800" },
  { value: "moyens",     label: "Moyens",          color: "bg-amber-100 text-amber-800" },
  { value: "qualite",    label: "Qualité",         color: "bg-rose-100 text-rose-800" },
];

// ── Helpers ───────────────────────────────────────────────────────────────────

function getCategoryConfig(value: string | null) {
  return CATEGORIES.find(c => c.value === value) ?? null;
}

function formatRelativeDate(iso: string | null): string {
  if (!iso) return "jamais";
  const diff = Date.now() - new Date(iso).getTime();
  const days = Math.floor(diff / 86400000);
  if (days === 0) return "aujourd'hui";
  if (days === 1) return "hier";
  if (days < 30) return `il y a ${days}j`;
  const months = Math.floor(days / 30);
  return `il y a ${months} mois`;
}

// ── Tag input chip component ───────────────────────────────────────────────────

function TagInput({
  tags,
  onChange,
}: {
  tags: string[];
  onChange: (tags: string[]) => void;
}) {
  const [input, setInput] = useState("");

  const addTag = () => {
    const val = input.trim().toLowerCase();
    if (val && !tags.includes(val)) {
      onChange([...tags, val]);
    }
    setInput("");
  };

  const removeTag = (tag: string) => onChange(tags.filter(t => t !== tag));

  return (
    <div className="flex flex-wrap gap-1.5 p-2 border border-slate-200 rounded-xl min-h-[42px] focus-within:ring-2 focus-within:ring-primary-500 focus-within:border-transparent transition-all">
      {tags.map(tag => (
        <span
          key={tag}
          className="inline-flex items-center gap-1 px-2 py-0.5 bg-primary-100 text-primary-800 rounded-full text-xs font-medium"
        >
          {tag}
          <button type="button" onClick={() => removeTag(tag)} className="hover:text-primary-600">
            <X className="w-3 h-3" />
          </button>
        </span>
      ))}
      <input
        type="text"
        value={input}
        onChange={e => setInput(e.target.value)}
        onKeyDown={e => {
          if (e.key === "Enter" || e.key === ",") {
            e.preventDefault();
            addTag();
          }
          if (e.key === "Backspace" && !input && tags.length) {
            onChange(tags.slice(0, -1));
          }
        }}
        onBlur={addTag}
        placeholder={tags.length === 0 ? "Ajouter un tag, appuyer sur Entrée…" : ""}
        className="flex-1 min-w-[120px] text-sm outline-none bg-transparent placeholder:text-slate-400"
      />
    </div>
  );
}

// ── Snippet Modal ─────────────────────────────────────────────────────────────

interface ModalProps {
  snippet?: Snippet | null;
  onClose: () => void;
  onSaved: () => void;
}

function SnippetModal({ snippet, onClose, onSaved }: ModalProps) {
  const isEdit = !!snippet;
  const [title, setTitle] = useState(snippet?.title ?? "");
  const [content, setContent] = useState(snippet?.content ?? "");
  const [tags, setTags] = useState<string[]>(snippet?.tags ?? []);
  const [category, setCategory] = useState<Category | "">(
    (snippet?.category as Category | null) ?? ""
  );

  const saveMutation = useMutation({
    mutationFn: async () => {
      const payload = {
        title: title.trim(),
        content,
        tags,
        category: category || null,
      };
      if (isEdit) {
        return libraryApi.update(snippet!.id, payload);
      }
      return libraryApi.create(payload);
    },
    onSuccess: () => {
      toast.success(isEdit ? "Snippet modifié" : "Snippet créé");
      onSaved();
      onClose();
    },
    onError: (err: Error) => toast.error(err.message || "Erreur lors de la sauvegarde"),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !content.trim()) return;
    saveMutation.mutate();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-fade-in">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-xl animate-slide-up">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-primary-100 flex items-center justify-center">
              <BookMarked className="w-3.5 h-3.5 text-primary-700" />
            </div>
            <p className="font-semibold text-slate-800 text-sm">
              {isEdit ? "Modifier le snippet" : "Nouveau snippet"}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="w-7 h-7 rounded-lg hover:bg-slate-100 flex items-center justify-center text-slate-400 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          {/* Title */}
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1.5">
              Titre <span className="text-danger-500">*</span>
            </label>
            <input
              type="text"
              value={title}
              onChange={e => setTitle(e.target.value)}
              placeholder="Ex : Présentation de l'équipe projet"
              maxLength={200}
              required
              className="w-full px-3 py-2 text-sm border border-slate-200 rounded-xl
                         focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
            />
          </div>

          {/* Category */}
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1.5">Catégorie</label>
            <div className="relative">
              <select
                value={category}
                onChange={e => setCategory(e.target.value as Category | "")}
                className="w-full px-3 py-2 text-sm border border-slate-200 rounded-xl focus:outline-none
                           focus:ring-2 focus:ring-primary-500 bg-white transition-all appearance-none pr-8"
              >
                <option value="">— Aucune catégorie —</option>
                {CATEGORIES.map(c => (
                  <option key={c.value} value={c.value}>{c.label}</option>
                ))}
              </select>
              <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
            </div>
          </div>

          {/* Tags */}
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1.5 flex items-center gap-1">
              <Tag className="w-3 h-3" />
              Tags
            </label>
            <TagInput tags={tags} onChange={setTags} />
          </div>

          {/* Content */}
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1.5">
              Contenu <span className="text-danger-500">*</span>
            </label>
            <textarea
              value={content}
              onChange={e => setContent(e.target.value)}
              placeholder="Rédigez ici votre texte réutilisable…"
              required
              rows={6}
              className="w-full px-3 py-2 text-sm border border-slate-200 rounded-xl
                         focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent
                         transition-all resize-none"
            />
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 pt-1">
            <button type="button" onClick={onClose} className="btn-secondary text-sm">
              Annuler
            </button>
            <button
              type="submit"
              disabled={saveMutation.isPending || !title.trim() || !content.trim()}
              className="btn-primary-gradient flex items-center gap-2"
            >
              {saveMutation.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
              {isEdit ? "Enregistrer" : "Créer le snippet"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ── Snippet Card ──────────────────────────────────────────────────────────────

function SnippetCard({
  snippet,
  onEdit,
  onDelete,
}: {
  snippet: Snippet;
  onEdit: () => void;
  onDelete: () => void;
}) {
  const [copied, setCopied] = useState(false);
  const queryClient = useQueryClient();

  const catConfig = getCategoryConfig(snippet.category);

  const useMutation_ = useMutation({
    mutationFn: () => libraryApi.use(snippet.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["library-snippets"] }),
  });

  const handleCopy = async () => {
    await navigator.clipboard.writeText(snippet.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    toast.success("Copié dans le presse-papier");
    useMutation_.mutate();
  };

  return (
    <div className="card p-4 flex flex-col gap-3 hover:shadow-md transition-shadow animate-fade-in">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <h3 className="text-sm font-semibold text-slate-800 leading-snug line-clamp-2">
            {snippet.title}
          </h3>

          <div className="flex flex-wrap items-center gap-1.5 mt-1.5">
            {catConfig && (
              <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${catConfig.color}`}>
                {catConfig.label}
              </span>
            )}
            {snippet.tags.map(tag => (
              <span
                key={tag}
                className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-slate-100 text-slate-600"
              >
                #{tag}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Content preview */}
      <p className="text-xs text-slate-500 leading-relaxed line-clamp-3">
        {snippet.content.length > 120
          ? `${snippet.content.slice(0, 120)}…`
          : snippet.content}
      </p>

      {/* Footer */}
      <div className="flex items-center justify-between pt-1 border-t border-slate-50">
        <p className="text-[10px] text-slate-400">
          Utilisé {snippet.usage_count} fois · {formatRelativeDate(snippet.last_used_at)}
        </p>

        <div className="flex items-center gap-1">
          {/* Copy */}
          <button
            onClick={handleCopy}
            title="Copier"
            className={`p-1.5 rounded-lg transition-all text-xs font-semibold flex items-center gap-1
              ${copied
                ? "bg-success-100 text-success-700"
                : "text-slate-400 hover:text-primary-600 hover:bg-primary-50"
              }`}
          >
            {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
          </button>

          {/* Edit */}
          <button
            onClick={onEdit}
            title="Modifier"
            className="p-1.5 rounded-lg text-slate-400 hover:text-primary-600 hover:bg-primary-50 transition-all"
          >
            <Pencil className="w-3.5 h-3.5" />
          </button>

          {/* Delete */}
          <button
            onClick={onDelete}
            title="Supprimer"
            className="p-1.5 rounded-lg text-slate-400 hover:text-danger-500 hover:bg-danger-50 transition-all"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Delete Confirm Modal ───────────────────────────────────────────────────────

function DeleteConfirm({
  snippet,
  onClose,
  onConfirm,
  isPending,
}: {
  snippet: Snippet;
  onClose: () => void;
  onConfirm: () => void;
  isPending: boolean;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-fade-in">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm animate-slide-up p-6 text-center">
        <div className="w-12 h-12 rounded-full bg-danger-100 flex items-center justify-center mx-auto mb-4">
          <Trash2 className="w-5 h-5 text-danger-600" />
        </div>
        <h3 className="font-semibold text-slate-800 mb-1">Supprimer ce snippet ?</h3>
        <p className="text-sm text-slate-500 mb-5">
          <span className="font-medium">&ldquo;{snippet.title}&rdquo;</span> sera définitivement supprimé.
        </p>
        <div className="flex gap-3 justify-center">
          <button onClick={onClose} className="btn-secondary text-sm px-5">Annuler</button>
          <button
            onClick={onConfirm}
            disabled={isPending}
            className="flex items-center gap-2 px-5 py-2 text-sm font-semibold bg-danger-600
                       text-white rounded-xl hover:bg-danger-700 transition-colors disabled:opacity-50"
          >
            {isPending && <Loader2 className="w-4 h-4 animate-spin" />}
            Supprimer
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function LibraryPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState<Category | "">("");
  const [showModal, setShowModal] = useState(false);
  const [editSnippet, setEditSnippet] = useState<Snippet | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Snippet | null>(null);

  // Fetch snippets
  const { data: snippets = [], isLoading } = useQuery<Snippet[]>({
    queryKey: ["library-snippets"],
    queryFn: () => libraryApi.list(),
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id: string) => libraryApi.delete(id),
    onSuccess: () => {
      toast.success("Snippet supprimé");
      setDeleteTarget(null);
      queryClient.invalidateQueries({ queryKey: ["library-snippets"] });
    },
    onError: () => toast.error("Impossible de supprimer ce snippet"),
  });

  // Client-side filtering (search + category)
  const filtered = useMemo(() => {
    return snippets.filter(s => {
      const matchCat = !categoryFilter || s.category === categoryFilter;
      const matchSearch =
        !search ||
        s.title.toLowerCase().includes(search.toLowerCase()) ||
        s.content.toLowerCase().includes(search.toLowerCase()) ||
        s.tags.some(t => t.toLowerCase().includes(search.toLowerCase()));
      return matchCat && matchSearch;
    });
  }, [snippets, search, categoryFilter]);

  return (
    <div className="p-6 md:p-8 max-w-6xl mx-auto">
      {/* ── Header ── */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-primary-600" />
            Bibliothèque de réponses
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            {snippets.length} snippet{snippets.length > 1 ? "s" : ""} enregistré{snippets.length > 1 ? "s" : ""}
          </p>
        </div>

        <button
          onClick={() => { setEditSnippet(null); setShowModal(true); }}
          className="btn-primary-gradient flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          Nouveau snippet
        </button>
      </div>

      {/* ── Filtres ── */}
      <div className="flex flex-col sm:flex-row gap-3 mb-6">
        {/* Search */}
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Rechercher…"
            className="w-full pl-9 pr-3 py-2 text-sm border border-slate-200 rounded-xl
                       focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
          />
          {search && (
            <button
              onClick={() => setSearch("")}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {/* Category pills */}
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() => setCategoryFilter("")}
            className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition-all
              ${categoryFilter === ""
                ? "bg-primary-700 text-white border-primary-700 shadow-sm"
                : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
              }`}
          >
            Tous
          </button>
          {CATEGORIES.map(cat => (
            <button
              key={cat.value}
              onClick={() => setCategoryFilter(categoryFilter === cat.value ? "" : cat.value)}
              className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition-all
                ${categoryFilter === cat.value
                  ? `${cat.color} border-transparent shadow-sm`
                  : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
                }`}
            >
              {cat.label}
            </button>
          ))}
        </div>
      </div>

      {/* ── Content ── */}
      {isLoading ? (
        <div className="flex items-center justify-center py-20 text-slate-400">
          <Loader2 className="w-6 h-6 animate-spin mr-2" />
          Chargement…
        </div>
      ) : snippets.length === 0 ? (
        /* Empty state */
        <div className="flex flex-col items-center justify-center py-20 text-center animate-fade-in">
          <div className="w-16 h-16 rounded-2xl bg-primary-50 flex items-center justify-center mb-4">
            <BookOpen className="w-7 h-7 text-primary-300" />
          </div>
          <h3 className="font-semibold text-slate-700 mb-1">Aucun snippet enregistré</h3>
          <p className="text-sm text-slate-400 mb-5 max-w-xs">
            Créez votre première réponse réutilisable pour gagner du temps lors de la rédaction de vos offres.
          </p>
          <button
            onClick={() => { setEditSnippet(null); setShowModal(true); }}
            className="btn-primary-gradient flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Créer votre premier snippet
          </button>
        </div>
      ) : filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-center text-slate-400">
          <Search className="w-8 h-8 mb-2 text-slate-200" />
          <p className="text-sm">Aucun snippet ne correspond à votre recherche</p>
          <button
            onClick={() => { setSearch(""); setCategoryFilter(""); }}
            className="mt-3 text-xs text-primary-600 hover:underline"
          >
            Réinitialiser les filtres
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filtered.map(snippet => (
            <SnippetCard
              key={snippet.id}
              snippet={snippet}
              onEdit={() => { setEditSnippet(snippet); setShowModal(true); }}
              onDelete={() => setDeleteTarget(snippet)}
            />
          ))}
        </div>
      )}

      {/* ── Modals ── */}
      {showModal && (
        <SnippetModal
          snippet={editSnippet}
          onClose={() => { setShowModal(false); setEditSnippet(null); }}
          onSaved={() => queryClient.invalidateQueries({ queryKey: ["library-snippets"] })}
        />
      )}

      {deleteTarget && (
        <DeleteConfirm
          snippet={deleteTarget}
          onClose={() => setDeleteTarget(null)}
          onConfirm={() => deleteMutation.mutate(deleteTarget.id)}
          isPending={deleteMutation.isPending}
        />
      )}
    </div>
  );
}
