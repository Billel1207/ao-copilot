"use client";

export const dynamic = "force-dynamic";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  Key, Webhook, Plus, Trash2, Eye, EyeOff, Copy, Check,
  Loader2, AlertCircle, ChevronDown, ChevronUp, Play,
  CheckCircle, XCircle, Code,
} from "lucide-react";
import api from "@/lib/api";

// Types
interface ApiKeyItem {
  id: string;
  name: string;
  key_prefix: string;
  can_read_projects: boolean;
  can_write_projects: boolean;
  can_read_analysis: boolean;
  can_trigger_analysis: boolean;
  is_active: boolean;
  last_used_at: string | null;
  created_at: string;
}
interface ApiKeyCreated extends ApiKeyItem { full_key: string; }
interface WebhookItem {
  id: string;
  url: string;
  description: string | null;
  events: string[];
  is_active: boolean;
  failure_count: number;
  last_delivery_at: string | null;
  created_at: string;
}
interface WebhookDelivery {
  id: string;
  event_type: string;
  status_code: number | null;
  success: boolean;
  error_message: string | null;
  delivered_at: string;
}

const ALL_EVENTS = [
  { value: "analysis.completed", label: "Analyse terminée" },
  { value: "project.created", label: "Projet créé" },
  { value: "project.deadline_due", label: "Deadline dans 7j" },
  { value: "quota.warning", label: "Alerte quota" },
  { value: "subscription.changed", label: "Changement d'abonnement" },
];

// API calls
const devApi = {
  listKeys: () => api.get("/developer/keys").then(r => r.data as ApiKeyItem[]),
  createKey: (d: { name: string; can_write_projects: boolean; can_trigger_analysis: boolean }) =>
    api.post("/developer/keys", d).then(r => r.data as ApiKeyCreated),
  revokeKey: (id: string) => api.delete(`/developer/keys/${id}`).then(r => r.data),
  listWebhooks: () => api.get("/developer/webhooks").then(r => r.data as WebhookItem[]),
  createWebhook: (d: { url: string; description?: string; events: string[] }) =>
    api.post("/developer/webhooks", d).then(r => r.data as WebhookItem),
  deleteWebhook: (id: string) => api.delete(`/developer/webhooks/${id}`).then(r => r.data),
  testWebhook: (id: string) => api.post(`/developer/webhooks/${id}/test`).then(r => r.data),
  listDeliveries: (id: string) =>
    api.get(`/developer/webhooks/${id}/deliveries`).then(r => r.data as WebhookDelivery[]),
};

export default function DeveloperPage() {
  const qc = useQueryClient();

  // State API Keys
  const [showCreateKey, setShowCreateKey] = useState(false);
  const [newKeyName, setNewKeyName] = useState("");
  const [newKeyWrite, setNewKeyWrite] = useState(false);
  const [newKeyTrigger, setNewKeyTrigger] = useState(false);
  const [createdKey, setCreatedKey] = useState<ApiKeyCreated | null>(null);
  const [keyVisible, setKeyVisible] = useState(false);
  const [keyCopied, setKeyCopied] = useState(false);

  // State Webhooks
  const [showCreateWebhook, setShowCreateWebhook] = useState(false);
  const [whUrl, setWhUrl] = useState("");
  const [whDesc, setWhDesc] = useState("");
  const [whEvents, setWhEvents] = useState(["analysis.completed", "project.created"]);
  const [expandedWebhook, setExpandedWebhook] = useState<string | null>(null);

  // Queries
  const { data: keys = [], isLoading: keysLoading } = useQuery({
    queryKey: ["dev-keys"],
    queryFn: devApi.listKeys,
  });
  const { data: webhooks = [], isLoading: whLoading } = useQuery({
    queryKey: ["dev-webhooks"],
    queryFn: devApi.listWebhooks,
  });
  const { data: deliveries = [] } = useQuery({
    queryKey: ["dev-deliveries", expandedWebhook],
    queryFn: () => devApi.listDeliveries(expandedWebhook!),
    enabled: !!expandedWebhook,
  });

  // Mutations
  const createKeyMut = useMutation({
    mutationFn: devApi.createKey,
    onSuccess: (data) => {
      setCreatedKey(data);
      setShowCreateKey(false);
      setNewKeyName("");
      setNewKeyWrite(false);
      setNewKeyTrigger(false);
      qc.invalidateQueries({ queryKey: ["dev-keys"] });
    },
    onError: () => toast.error("Erreur lors de la creation de la cle"),
  });
  const revokeKeyMut = useMutation({
    mutationFn: devApi.revokeKey,
    onSuccess: () => {
      toast.success("Cle revoquee");
      qc.invalidateQueries({ queryKey: ["dev-keys"] });
    },
  });
  const createWhMut = useMutation({
    mutationFn: devApi.createWebhook,
    onSuccess: () => {
      toast.success("Webhook cree");
      setShowCreateWebhook(false);
      setWhUrl("");
      setWhDesc("");
      setWhEvents(["analysis.completed", "project.created"]);
      qc.invalidateQueries({ queryKey: ["dev-webhooks"] });
    },
    onError: () => toast.error("Erreur lors de la creation du webhook"),
  });
  const deleteWhMut = useMutation({
    mutationFn: devApi.deleteWebhook,
    onSuccess: () => {
      toast.success("Webhook supprime");
      qc.invalidateQueries({ queryKey: ["dev-webhooks"] });
    },
  });
  const testWhMut = useMutation({
    mutationFn: devApi.testWebhook,
    onSuccess: () => {
      toast.success("Evenement test envoye !");
      if (expandedWebhook) {
        qc.invalidateQueries({ queryKey: ["dev-deliveries", expandedWebhook] });
      }
    },
    onError: () => toast.error("Echec de l'envoi test"),
  });

  const copyKey = () => {
    if (createdKey) {
      navigator.clipboard.writeText(createdKey.full_key);
      setKeyCopied(true);
      setTimeout(() => setKeyCopied(false), 2000);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Developpeur &amp; Integrations</h1>
        <p className="text-slate-500 text-sm mt-1">
          Gerez vos cles API et webhooks pour integrer AO Copilot avec vos outils.
        </p>
      </div>

      {/* Cle creee - alerte copie */}
      {createdKey && (
        <div className="bg-amber-50 border border-amber-300 rounded-2xl p-5">
          <div className="flex items-start gap-3 mb-3">
            <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-amber-800">Copiez votre cle maintenant !</p>
              <p className="text-sm text-amber-600">Elle ne sera plus affichee apres cette fenetre.</p>
            </div>
          </div>
          <div className="flex items-center gap-2 bg-white border border-amber-200 rounded-xl px-4 py-3 font-mono text-sm">
            <span className="flex-1 truncate">
              {keyVisible
                ? createdKey.full_key
                : createdKey.full_key.replace(/./g, "•")}
            </span>
            <button onClick={() => setKeyVisible(!keyVisible)} className="text-amber-500 hover:text-amber-700">
              {keyVisible ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
            <button onClick={copyKey} className="text-amber-500 hover:text-amber-700">
              {keyCopied ? <Check className="w-4 h-4 text-green-600" /> : <Copy className="w-4 h-4" />}
            </button>
          </div>
          <button
            onClick={() => setCreatedKey(null)}
            className="mt-3 text-xs text-amber-500 hover:underline"
          >
            J&apos;ai copie ma cle, fermer
          </button>
        </div>
      )}

      {/* Section Cles API */}
      <section className="bg-white rounded-2xl border border-slate-200 p-6">
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-blue-50 rounded-xl flex items-center justify-center">
              <Key className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h2 className="font-semibold text-slate-900">Cles API</h2>
              <p className="text-xs text-slate-400">Pour acces programmatique a l&apos;API REST</p>
            </div>
          </div>
          <button
            onClick={() => setShowCreateKey(!showCreateKey)}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-xl transition-colors"
          >
            <Plus className="w-4 h-4" /> Creer une cle
          </button>
        </div>

        {showCreateKey && (
          <div className="bg-slate-50 rounded-xl p-4 mb-4 space-y-3">
            <input
              value={newKeyName}
              onChange={e => setNewKeyName(e.target.value)}
              placeholder="Nom de la cle (ex: Mon ERP, Integration Acumatica)"
              className="w-full px-3 py-2 text-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <div className="flex flex-wrap gap-4 text-sm">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={newKeyWrite}
                  onChange={e => setNewKeyWrite(e.target.checked)}
                  className="rounded border-slate-300 text-blue-600"
                />
                Ecriture projets
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={newKeyTrigger}
                  onChange={e => setNewKeyTrigger(e.target.checked)}
                  className="rounded border-slate-300 text-blue-600"
                />
                Declencher analyses
              </label>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => createKeyMut.mutate({
                  name: newKeyName,
                  can_write_projects: newKeyWrite,
                  can_trigger_analysis: newKeyTrigger,
                })}
                disabled={!newKeyName || createKeyMut.isPending}
                className="flex items-center gap-1.5 px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-xl transition-colors disabled:opacity-50"
              >
                {createKeyMut.isPending && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                Generer
              </button>
              <button
                onClick={() => setShowCreateKey(false)}
                className="px-4 py-2 text-sm text-slate-500 hover:bg-slate-100 rounded-xl transition-colors"
              >
                Annuler
              </button>
            </div>
          </div>
        )}

        {keysLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-5 h-5 animate-spin text-slate-400" />
          </div>
        ) : keys.length === 0 ? (
          <p className="text-center text-slate-400 text-sm py-8">Aucune cle API creee</p>
        ) : (
          <div className="space-y-2">
            {keys.map(k => (
              <div key={k.id} className="flex items-center justify-between p-3 bg-slate-50 rounded-xl">
                <div className="flex items-center gap-3 min-w-0">
                  <Key className="w-4 h-4 text-slate-400 flex-shrink-0" />
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-slate-800 truncate">{k.name}</p>
                    <p className="text-xs text-slate-400 font-mono">{k.key_prefix}••••••••</p>
                  </div>
                  <div className="flex gap-1 flex-shrink-0">
                    {k.can_write_projects && (
                      <span className="text-[10px] bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded">
                        ecriture
                      </span>
                    )}
                    {k.can_trigger_analysis && (
                      <span className="text-[10px] bg-purple-100 text-purple-700 px-1.5 py-0.5 rounded">
                        analyse
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-3 flex-shrink-0">
                  <span className="text-xs text-slate-400">
                    {k.last_used_at
                      ? `Derniere utilisation ${new Date(k.last_used_at).toLocaleDateString("fr-FR")}`
                      : "Jamais utilisee"}
                  </span>
                  <button
                    onClick={() => revokeKeyMut.mutate(k.id)}
                    disabled={revokeKeyMut.isPending}
                    className="p-1.5 text-red-400 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50"
                    title="Revoquer"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Section Webhooks */}
      <section className="bg-white rounded-2xl border border-slate-200 p-6">
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-green-50 rounded-xl flex items-center justify-center">
              <Webhook className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <h2 className="font-semibold text-slate-900">Webhooks</h2>
              <p className="text-xs text-slate-400">Notifications HTTP automatiques vers vos systemes</p>
            </div>
          </div>
          <button
            onClick={() => setShowCreateWebhook(!showCreateWebhook)}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-xl transition-colors"
          >
            <Plus className="w-4 h-4" /> Ajouter
          </button>
        </div>

        {showCreateWebhook && (
          <div className="bg-slate-50 rounded-xl p-4 mb-4 space-y-3">
            <input
              value={whUrl}
              onChange={e => setWhUrl(e.target.value)}
              placeholder="https://votre-erp.com/webhook/ao-copilot"
              className="w-full px-3 py-2 text-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <input
              value={whDesc}
              onChange={e => setWhDesc(e.target.value)}
              placeholder="Description (optionnel)"
              className="w-full px-3 py-2 text-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <div>
              <p className="text-xs font-medium text-slate-600 mb-2">Evenements</p>
              <div className="flex flex-wrap gap-3">
                {ALL_EVENTS.map(ev => (
                  <label key={ev.value} className="flex items-center gap-1.5 text-xs cursor-pointer">
                    <input
                      type="checkbox"
                      checked={whEvents.includes(ev.value)}
                      onChange={() =>
                        setWhEvents(prev =>
                          prev.includes(ev.value)
                            ? prev.filter(e => e !== ev.value)
                            : [...prev, ev.value]
                        )
                      }
                      className="rounded border-slate-300 text-blue-600"
                    />
                    {ev.label}
                  </label>
                ))}
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() =>
                  createWhMut.mutate({ url: whUrl, description: whDesc || undefined, events: whEvents })
                }
                disabled={!whUrl || whEvents.length === 0 || createWhMut.isPending}
                className="flex items-center gap-1.5 px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-xl transition-colors disabled:opacity-50"
              >
                {createWhMut.isPending && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                Creer
              </button>
              <button
                onClick={() => setShowCreateWebhook(false)}
                className="px-4 py-2 text-sm text-slate-500 hover:bg-slate-100 rounded-xl transition-colors"
              >
                Annuler
              </button>
            </div>
          </div>
        )}

        {whLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-5 h-5 animate-spin text-slate-400" />
          </div>
        ) : webhooks.length === 0 ? (
          <p className="text-center text-slate-400 text-sm py-8">Aucun webhook configure</p>
        ) : (
          <div className="space-y-3">
            {webhooks.map(wh => (
              <div key={wh.id} className="border border-slate-200 rounded-xl overflow-hidden">
                <div className="flex items-center justify-between p-3 bg-slate-50">
                  <div className="flex items-center gap-3 min-w-0">
                    <div
                      className={`w-2 h-2 rounded-full flex-shrink-0 ${wh.is_active ? "bg-green-500" : "bg-slate-300"}`}
                    />
                    <div className="min-w-0">
                      <p className="text-sm font-mono text-slate-700 truncate">{wh.url}</p>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {wh.events.map(ev => (
                          <span key={ev} className="text-[10px] bg-slate-200 text-slate-600 px-1.5 rounded">
                            {ev}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-1 flex-shrink-0">
                    <button
                      onClick={() => testWhMut.mutate(wh.id)}
                      disabled={testWhMut.isPending}
                      className="p-1.5 text-green-500 hover:bg-green-50 rounded-lg transition-colors disabled:opacity-50"
                      title="Tester"
                    >
                      <Play className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() =>
                        setExpandedWebhook(expandedWebhook === wh.id ? null : wh.id)
                      }
                      className="p-1.5 text-slate-400 hover:bg-slate-100 rounded-lg transition-colors"
                    >
                      {expandedWebhook === wh.id ? (
                        <ChevronUp className="w-4 h-4" />
                      ) : (
                        <ChevronDown className="w-4 h-4" />
                      )}
                    </button>
                    <button
                      onClick={() => deleteWhMut.mutate(wh.id)}
                      disabled={deleteWhMut.isPending}
                      className="p-1.5 text-red-400 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {expandedWebhook === wh.id && (
                  <div className="p-3 border-t border-slate-200">
                    <p className="text-xs font-medium text-slate-600 mb-2">Dernieres livraisons</p>
                    {deliveries.length === 0 ? (
                      <p className="text-xs text-slate-400 italic">Aucune livraison</p>
                    ) : (
                      <div className="space-y-1.5 max-h-48 overflow-y-auto">
                        {deliveries.map(d => (
                          <div key={d.id} className="flex items-center gap-2 text-xs">
                            {d.success ? (
                              <CheckCircle className="w-3.5 h-3.5 text-green-500 flex-shrink-0" />
                            ) : (
                              <XCircle className="w-3.5 h-3.5 text-red-500 flex-shrink-0" />
                            )}
                            <span className="font-mono text-slate-500">
                              {new Date(d.delivered_at).toLocaleTimeString("fr-FR")}
                            </span>
                            <span className="bg-slate-100 px-1 rounded">{d.event_type}</span>
                            {d.status_code && (
                              <span className={d.success ? "text-green-600" : "text-red-600"}>
                                {d.status_code}
                              </span>
                            )}
                            {d.error_message && (
                              <span className="text-red-500 truncate">{d.error_message}</span>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Documentation rapide */}
      <section className="bg-slate-900 rounded-2xl p-6 text-white">
        <div className="flex items-center gap-3 mb-4">
          <Code className="w-5 h-5 text-slate-400" />
          <h2 className="font-semibold">Documentation rapide</h2>
        </div>
        <div className="space-y-4 text-sm">
          <div>
            <p className="text-slate-400 text-xs mb-2">Authentification via header :</p>
            <code className="block bg-slate-800 rounded-lg p-3 font-mono text-green-400 text-xs">
              Authorization: Bearer aoc_votre_cle_api
            </code>
          </div>
          <div>
            <p className="text-slate-400 text-xs mb-2">Format d&apos;evenement webhook :</p>
            <pre className="bg-slate-800 rounded-lg p-3 font-mono text-green-400 text-xs overflow-x-auto">{`{
  "id": "evt_...",
  "event": "analysis.completed",
  "created_at": "2026-03-08T10:00:00Z",
  "org_id": "uuid-...",
  "data": { "project_id": "uuid-...", ... }
}`}</pre>
          </div>
          <div>
            <p className="text-slate-400 text-xs mb-2">Verification signature webhook :</p>
            <code className="block bg-slate-800 rounded-lg p-3 font-mono text-green-400 text-xs">
              X-AO-Signature: sha256=&lt;hmac-sha256-du-payload&gt;
            </code>
          </div>
          <div>
            <p className="text-slate-400 text-xs mb-2">Exemple : lister les projets :</p>
            <pre className="bg-slate-800 rounded-lg p-3 font-mono text-green-400 text-xs overflow-x-auto">{`curl https://app.aocopilot.fr/api/v1/projects \\
  -H "Authorization: Bearer aoc_votre_cle_api"`}</pre>
          </div>
        </div>
      </section>
    </div>
  );
}
