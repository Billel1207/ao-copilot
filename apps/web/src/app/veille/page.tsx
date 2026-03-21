"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  Bell, RefreshCw, ChevronDown, ChevronUp, Save,
  Calendar, Euro, Building2, MapPin, Tag, Eye,
  Plus, Loader2, AlertCircle, Search, Filter,
} from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { veilleApi, projectsApi } from "@/lib/api";
import { formatDate } from "@/lib/utils";

// ── Types ──────────────────────────────────────────────────────────────────────

interface WatchConfig {
  id: string;
  keywords: string[];
  regions: string[];
  cpv_codes: string[];
  min_budget_eur: number | null;
  max_budget_eur: number | null;
  is_active: boolean;
  ted_enabled: boolean;
  last_checked_at: string | null;
}

interface WatchResult {
  id: string;
  source: string;
  boamp_ref: string;
  title: string;
  buyer: string | null;
  region: string | null;
  publication_date: string | null;
  deadline_date: string | null;
  estimated_value_eur: number | null;
  procedure: string | null;
  cpv_codes: string[];
  url: string | null;
  is_read: boolean;
  created_at: string;
}

interface WatchResultList {
  items: WatchResult[];
  total: number;
  unread_count: number;
}

// ── Régions françaises ─────────────────────────────────────────────────────────

const FRENCH_REGIONS = [
  "Auvergne-Rhône-Alpes",
  "Bourgogne-Franche-Comté",
  "Bretagne",
  "Centre-Val de Loire",
  "Corse",
  "Grand Est",
  "Guadeloupe",
  "Guyane",
  "Hauts-de-France",
  "Ile-de-France",
  "La Réunion",
  "Martinique",
  "Mayotte",
  "Normandie",
  "Nouvelle-Aquitaine",
  "Occitanie",
  "Pays de la Loire",
  "Provence-Alpes-Côte d'Azur",
];

// ── Sous-composants ─────────────────────────────────────────────────────────────

function KeywordChips({
  keywords,
  onChange,
}: {
  keywords: string[];
  onChange: (kw: string[]) => void;
}) {
  const [input, setInput] = useState("");

  const addKeyword = () => {
    const trimmed = input.trim();
    if (trimmed && !keywords.includes(trimmed)) {
      onChange([...keywords, trimmed]);
    }
    setInput("");
  };

  const removeKeyword = (kw: string) => {
    onChange(keywords.filter((k) => k !== kw));
  };

  return (
    <div>
      <label className="block text-xs font-medium text-slate-600 mb-1.5">
        Mots-clés
      </label>
      <div className="flex flex-wrap gap-1.5 mb-2 min-h-[32px]">
        {keywords.map((kw) => (
          <span
            key={kw}
            className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-800"
          >
            {kw}
            <button
              type="button"
              onClick={() => removeKeyword(kw)}
              className="hover:text-primary-600 ml-0.5 leading-none"
              aria-label={`Supprimer ${kw}`}
            >
              ×
            </button>
          </span>
        ))}
        {keywords.length === 0 && (
          <span className="text-xs text-slate-400 self-center">Aucun mot-clé ajouté</span>
        )}
      </div>
      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") { e.preventDefault(); addKeyword(); }
          }}
          placeholder="Ex: VRD, terrassement, génie civil..."
          className="flex-1 text-sm border border-slate-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
        />
        <button
          type="button"
          onClick={addKeyword}
          className="px-3 py-1.5 bg-primary-50 text-primary-700 rounded-lg text-xs font-medium hover:bg-primary-100 transition-colors border border-primary-200"
        >
          <Plus className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
}

function AoCard({
  result,
  onMarkRead,
  onAnalyze,
}: {
  result: WatchResult;
  onMarkRead: (id: string) => void;
  onAnalyze: (result: WatchResult) => void;
}) {
  const now = Date.now();
  const deadlineMs = result.deadline_date ? new Date(result.deadline_date).getTime() : null;
  const isUrgent = deadlineMs !== null && deadlineMs - now < 7 * 86400_000 && deadlineMs > now;
  const isPast = deadlineMs !== null && deadlineMs < now;

  const formatBudget = (val: number | null) => {
    if (!val) return null;
    return new Intl.NumberFormat("fr-FR", {
      style: "currency",
      currency: "EUR",
      maximumFractionDigits: 0,
    }).format(val);
  };

  return (
    <div
      className={`card p-4 border-l-4 animate-fade-in transition-all duration-150
        ${result.is_read
          ? "border-l-slate-200 opacity-80"
          : "border-l-primary-600 shadow-card-hover"
        }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          {/* Titre + badge nouveau */}
          <div className="flex items-start gap-2 mb-1">
            {!result.is_read && (
              <span className="flex-shrink-0 mt-0.5 inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold bg-primary-600 text-white uppercase tracking-wide">
                Nouveau
              </span>
            )}
            <p className="font-semibold text-slate-900 text-sm leading-snug line-clamp-2">
              {result.title}
            </p>
          </div>

          {/* Métadonnées */}
          <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2">
            {result.buyer && (
              <span className="flex items-center gap-1 text-xs text-slate-500">
                <Building2 className="w-3 h-3 flex-shrink-0" />
                <span className="truncate max-w-[200px]">{result.buyer}</span>
              </span>
            )}
            {result.region && (
              <span className="flex items-center gap-1 text-xs text-slate-500">
                <MapPin className="w-3 h-3 flex-shrink-0" />
                {result.region}
              </span>
            )}
            {result.estimated_value_eur && (
              <span className="flex items-center gap-1 text-xs text-slate-600 font-medium">
                <Euro className="w-3 h-3 flex-shrink-0" />
                {formatBudget(result.estimated_value_eur)}
              </span>
            )}
            {result.procedure && (
              <span className="flex items-center gap-1 text-xs text-slate-400">
                <Tag className="w-3 h-3 flex-shrink-0" />
                {result.procedure}
              </span>
            )}
          </div>

          {/* Date limite */}
          {result.deadline_date && (
            <div className="mt-2">
              <span
                className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full
                  ${isPast
                    ? "bg-slate-100 text-slate-400"
                    : isUrgent
                      ? "bg-red-100 text-red-700"
                      : "bg-slate-100 text-slate-600"
                  }`}
              >
                <Calendar className="w-3 h-3" />
                Limite : {formatDate(result.deadline_date)}
                {isUrgent && <span className="font-bold ml-0.5">— Urgent</span>}
                {isPast && <span className="ml-0.5">— Expiré</span>}
              </span>
            </div>
          )}
        </div>

        {/* Source + Réf */}
        <div className="flex-shrink-0 text-right flex flex-col items-end gap-1">
          {result.source === "TED" ? (
            <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold bg-yellow-100 text-yellow-700 uppercase tracking-wide">
              TED
            </span>
          ) : (
            <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold bg-blue-100 text-blue-700 uppercase tracking-wide">
              BOAMP
            </span>
          )}
          <span className="text-[10px] text-slate-300 font-mono">{result.boamp_ref}</span>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 mt-3 pt-3 border-t border-slate-100">
        {result.url && (
          <a
            href={result.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-primary-600 hover:text-primary-800 underline-offset-2 hover:underline font-medium"
          >
            {result.source === "TED" ? "Voir l\u2019annonce TED" : "Voir l\u2019annonce BOAMP"}
          </a>
        )}
        <div className="flex items-center gap-2 ml-auto">
          {!result.is_read && (
            <button
              type="button"
              onClick={() => onMarkRead(result.id)}
              className="inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-700 px-2.5 py-1.5 rounded-lg hover:bg-slate-100 transition-colors"
            >
              <Eye className="w-3.5 h-3.5" />
              Marquer lu
            </button>
          )}
          <button
            type="button"
            onClick={() => onAnalyze(result)}
            className="btn-primary-gradient inline-flex items-center gap-1.5 text-xs py-1.5 px-3"
          >
            <Plus className="w-3.5 h-3.5" />
            Analyser cet AO
          </button>
        </div>
      </div>
    </div>
  );
}

function EmptyVeille({ hasConfig }: { hasConfig: boolean }) {
  return (
    <div className="empty-state animate-fade-in py-16">
      <div className="w-16 h-16 rounded-2xl bg-primary-50 flex items-center justify-center mx-auto mb-4">
        <Bell className="w-8 h-8 text-primary-400" />
      </div>
      <h3 className="text-slate-700 font-semibold text-lg">
        {hasConfig
          ? "Aucun appel d'offres pour l'instant"
          : "Configurez votre veille pour recevoir des alertes AO"}
      </h3>
      <p className="text-slate-400 text-sm mt-1 max-w-xs mx-auto">
        {hasConfig
          ? "Lancez une synchronisation ou attendez la prochaine mise à jour automatique."
          : "Renseignez vos mots-clés, régions et critères budgétaires, puis sauvegardez."}
      </p>
    </div>
  );
}

// ── Page principale ─────────────────────────────────────────────────────────────

export default function VeillePage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [configOpen, setConfigOpen] = useState(false);
  const [filterUnread, setFilterUnread] = useState<boolean | undefined>(undefined);

  // Config state locale
  const [keywords, setKeywords] = useState<string[]>([]);
  const [regions, setRegions] = useState<string[]>([]);
  const [cpvInput, setCpvInput] = useState("");
  const [cpvCodes, setCpvCodes] = useState<string[]>([]);
  const [minBudget, setMinBudget] = useState<string>("");
  const [maxBudget, setMaxBudget] = useState<string>("");
  const [tedEnabled, setTedEnabled] = useState<boolean>(false);
  const [configInitialized, setConfigInitialized] = useState(false);
  const [syncMsg, setSyncMsg] = useState<string | null>(null);

  // ── Queries ─────────────────────────────────────────────────────────────────
  const { data: configData, isLoading: configLoading } = useQuery<WatchConfig | null>({
    queryKey: ["veille-config"],
    queryFn: () => veilleApi.getConfig().then((r) => r.data as WatchConfig | null),
  });

  // Initialiser les champs du formulaire depuis les données serveur (une seule fois)
  useEffect(() => {
    if (configData && !configInitialized) {
      setKeywords(configData.keywords ?? []);
      setRegions(configData.regions ?? []);
      setCpvCodes(configData.cpv_codes ?? []);
      setMinBudget(configData.min_budget_eur?.toString() ?? "");
      setMaxBudget(configData.max_budget_eur?.toString() ?? "");
      setTedEnabled(configData.ted_enabled ?? false);
      setConfigInitialized(true);
    }
  }, [configData, configInitialized]);

  const { data: resultsData, isLoading: resultsLoading } = useQuery({
    queryKey: ["veille-results", filterUnread],
    queryFn: () =>
      veilleApi
        .getResults(filterUnread !== undefined ? { is_read: filterUnread } : undefined)
        .then((r) => r.data as WatchResultList),
    refetchInterval: 60_000, // rafraichissement auto toutes les 60s
  });

  // ── Mutations ────────────────────────────────────────────────────────────────
  const saveConfigMutation = useMutation({
    mutationFn: () =>
      veilleApi.updateConfig({
        keywords,
        regions,
        cpv_codes: cpvCodes,
        min_budget_eur: minBudget ? parseInt(minBudget, 10) : null,
        max_budget_eur: maxBudget ? parseInt(maxBudget, 10) : null,
        is_active: true,
        ted_enabled: tedEnabled,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["veille-config"] });
      setConfigOpen(false);
    },
  });

  const markReadMutation = useMutation({
    mutationFn: (id: string) => veilleApi.markRead(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["veille-results"] });
    },
  });

  const syncMutation = useMutation({
    mutationFn: () => veilleApi.sync(),
    onSuccess: () => {
      setSyncMsg("Synchronisation lancée. Les résultats arrivent dans quelques secondes.");
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ["veille-results"] });
        setSyncMsg(null);
      }, 4000);
    },
  });

  // ── Handler "Analyser cet AO" ────────────────────────────────────────────────
  const handleAnalyze = async (result: WatchResult) => {
    try {
      const resp = await projectsApi.create({
        title: result.title.slice(0, 500),
        buyer: result.buyer ?? undefined,
        reference: result.boamp_ref,
      });
      const newProjectId = resp.data?.id;
      if (newProjectId) {
        router.push(`/projects/${newProjectId}`);
      }
    } catch {
      // silently ignore — l'utilisateur peut créer manuellement
    }
  };

  // ── Dérivés ──────────────────────────────────────────────────────────────────
  const hasConfig = !!configData;
  const unreadCount = resultsData?.unread_count ?? 0;
  const results = resultsData?.items ?? [];

  const toggleRegion = (region: string) => {
    setRegions((prev) =>
      prev.includes(region) ? prev.filter((r) => r !== region) : [...prev, region]
    );
  };

  const addCpv = () => {
    const trimmed = cpvInput.trim();
    if (trimmed && !cpvCodes.includes(trimmed)) {
      setCpvCodes((prev) => [...prev, trimmed]);
    }
    setCpvInput("");
  };

  return (
    <div className="p-6 md:p-8 max-w-5xl mx-auto space-y-6">
      {/* ── Header ── */}
      <div className="flex items-start justify-between animate-fade-in">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Bell className="w-6 h-6 text-primary-600" />
            Veille Appels d&apos;Offres
            {unreadCount > 0 && (
              <span className="inline-flex items-center justify-center px-2 py-0.5 rounded-full text-xs font-bold bg-primary-600 text-white min-w-[22px]">
                {unreadCount > 99 ? "99+" : unreadCount}
              </span>
            )}
          </h1>
          <p className="text-slate-400 text-sm mt-0.5">
            Surveillance automatique des AO BOAMP selon vos critères
            {configData?.last_checked_at && (
              <span className="ml-2 text-slate-300">
                — Dernière sync : {formatDate(configData.last_checked_at)}
              </span>
            )}
          </p>
        </div>
        <button
          type="button"
          onClick={() => syncMutation.mutate()}
          disabled={syncMutation.isPending || !hasConfig}
          className="btn-primary-gradient flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {syncMutation.isPending ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <RefreshCw className="w-4 h-4" />
          )}
          <span className="hidden sm:inline">Sync maintenant</span>
        </button>
      </div>

      {/* ── Message sync ── */}
      {syncMsg && (
        <div className="flex items-center gap-2 p-3 rounded-xl bg-success-50 border border-success-200 text-success-700 text-sm animate-fade-in">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          {syncMsg}
        </div>
      )}

      {/* ── Section configuration (collapsible) ── */}
      <div className="card overflow-hidden animate-slide-up">
        <button
          type="button"
          onClick={() => setConfigOpen((o) => !o)}
          className="w-full flex items-center justify-between p-4 hover:bg-slate-50 transition-colors"
        >
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-primary-600" />
            <span className="font-semibold text-slate-800 text-sm">
              Configuration de la veille
            </span>
            {hasConfig && (
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium bg-success-100 text-success-700">
                Active
              </span>
            )}
            {!hasConfig && !configLoading && (
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium bg-warning-100 text-warning-700">
                Non configurée
              </span>
            )}
          </div>
          {configOpen ? (
            <ChevronUp className="w-4 h-4 text-slate-400" />
          ) : (
            <ChevronDown className="w-4 h-4 text-slate-400" />
          )}
        </button>

        {configOpen && (
          <div className="border-t border-slate-100 p-4 space-y-5 animate-fade-in">
            {/* Mots-clés */}
            <KeywordChips keywords={keywords} onChange={setKeywords} />

            {/* Régions */}
            <div>
              <label className="block text-xs font-medium text-slate-600 mb-2">
                Régions ({regions.length} sélectionnée{regions.length > 1 ? "s" : ""})
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5">
                {FRENCH_REGIONS.map((region) => (
                  <label key={region} className="flex items-center gap-2 cursor-pointer group">
                    <input
                      type="checkbox"
                      checked={regions.includes(region)}
                      onChange={() => toggleRegion(region)}
                      className="rounded border-slate-300 text-primary-600 focus:ring-primary-500"
                    />
                    <span className="text-xs text-slate-600 group-hover:text-slate-900 transition-colors">
                      {region}
                    </span>
                  </label>
                ))}
              </div>
            </div>

            {/* Codes CPV */}
            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1.5">
                Codes CPV
              </label>
              <div className="flex flex-wrap gap-1.5 mb-2">
                {cpvCodes.map((cpv) => (
                  <span
                    key={cpv}
                    className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800"
                  >
                    {cpv}
                    <button
                      type="button"
                      onClick={() => setCpvCodes((prev) => prev.filter((c) => c !== cpv))}
                      className="hover:text-amber-600 ml-0.5 leading-none"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={cpvInput}
                  onChange={(e) => setCpvInput(e.target.value)}
                  onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); addCpv(); } }}
                  placeholder="Ex: 45000000 (Travaux), 71000000 (Services ingénierie)"
                  className="flex-1 text-sm border border-slate-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
                <button
                  type="button"
                  onClick={addCpv}
                  className="px-3 py-1.5 bg-amber-50 text-amber-700 rounded-lg text-xs font-medium hover:bg-amber-100 transition-colors border border-amber-200"
                >
                  <Plus className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            {/* Budget */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1.5">
                  Budget minimum (€)
                </label>
                <input
                  type="number"
                  value={minBudget}
                  onChange={(e) => setMinBudget(e.target.value)}
                  placeholder="Ex: 50000"
                  min={0}
                  className="w-full text-sm border border-slate-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1.5">
                  Budget maximum (€)
                </label>
                <input
                  type="number"
                  value={maxBudget}
                  onChange={(e) => setMaxBudget(e.target.value)}
                  placeholder="Ex: 5000000"
                  min={0}
                  className="w-full text-sm border border-slate-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>
            </div>

            {/* Monitoring TED (appels d'offres européens) */}
            <div className="flex items-center justify-between p-3 rounded-xl bg-yellow-50 border border-yellow-200">
              <div className="flex flex-col">
                <span className="text-sm font-medium text-yellow-900">
                  Inclure les appels d&apos;offres européens (TED)
                </span>
                <span className="text-xs text-yellow-700 mt-0.5">
                  Surveille le portail TED (UE) — France, Belgique (Wallonie), Luxembourg
                </span>
              </div>
              <button
                type="button"
                role="switch"
                aria-checked={tedEnabled}
                onClick={() => setTedEnabled((v) => !v)}
                className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:ring-offset-2
                  ${tedEnabled ? "bg-yellow-500" : "bg-slate-200"}`}
              >
                <span
                  className={`inline-block h-5 w-5 transform rounded-full bg-white shadow-sm transition duration-200
                    ${tedEnabled ? "translate-x-5" : "translate-x-0"}`}
                />
              </button>
            </div>

            {/* Bouton sauvegarder */}
            <div className="flex justify-end pt-1">
              <button
                type="button"
                onClick={() => saveConfigMutation.mutate()}
                disabled={saveConfigMutation.isPending}
                className="btn-primary-gradient flex items-center gap-2 disabled:opacity-60"
              >
                {saveConfigMutation.isPending ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Save className="w-4 h-4" />
                )}
                Sauvegarder la configuration
              </button>
            </div>
          </div>
        )}
      </div>

      {/* ── Filtres résultats ── */}
      {results.length > 0 || filterUnread !== undefined ? (
        <div className="flex items-center gap-2">
          <Search className="w-4 h-4 text-slate-400" />
          <span className="text-xs text-slate-500 font-medium mr-1">Filtrer :</span>
          <button
            type="button"
            onClick={() => setFilterUnread(undefined)}
            className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-colors
              ${filterUnread === undefined
                ? "bg-primary-600 text-white"
                : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
          >
            Tous ({resultsData?.total ?? 0})
          </button>
          <button
            type="button"
            onClick={() => setFilterUnread(false)}
            className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-colors
              ${filterUnread === false
                ? "bg-primary-600 text-white"
                : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
          >
            Non lus ({unreadCount})
          </button>
          <button
            type="button"
            onClick={() => setFilterUnread(true)}
            className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-colors
              ${filterUnread === true
                ? "bg-slate-700 text-white"
                : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
          >
            Lus
          </button>
        </div>
      ) : null}

      {/* ── Feed AO ── */}
      <div className="space-y-3">
        {resultsLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="card p-4 animate-pulse">
                <div className="h-4 bg-slate-200 rounded w-3/4 mb-3" />
                <div className="h-3 bg-slate-100 rounded w-1/2 mb-2" />
                <div className="h-3 bg-slate-100 rounded w-1/4" />
              </div>
            ))}
          </div>
        ) : results.length === 0 ? (
          <EmptyVeille hasConfig={hasConfig} />
        ) : (
          results.map((result) => (
            <AoCard
              key={result.id}
              result={result}
              onMarkRead={(id) => markReadMutation.mutate(id)}
              onAnalyze={handleAnalyze}
            />
          ))
        )}
      </div>
    </div>
  );
}
