"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Shield,
  ShieldCheck,
  ShieldX,
  ShieldAlert,
  RefreshCw,
  Loader2,
  AlertCircle,
} from "lucide-react";
import { attestationsApi } from "@/lib/api";

interface Attestation {
  type: string;
  status: "valid" | "expired" | "missing" | "unknown" | "mock";
  expires_at: string | null;
  document_url: string | null;
  details: string | null;
  is_mock: boolean;
}

interface AttestationsData {
  siret: string;
  checked_at: string;
  attestations: Attestation[];
}

const TYPE_LABELS: Record<string, string> = {
  attestation_fiscale: "Attestation fiscale (DGFiP)",
  attestation_urssaf: "Attestation de vigilance URSSAF",
  assurance_decennale: "Assurance décennale RC Pro",
  kbis: "Extrait Kbis",
};

const STATUS_CONFIG: Record<
  string,
  { icon: typeof Shield; color: string; bg: string; label: string }
> = {
  valid: {
    icon: ShieldCheck,
    color: "text-green-600",
    bg: "bg-green-50 border-green-200",
    label: "Valide",
  },
  expired: {
    icon: ShieldX,
    color: "text-red-600",
    bg: "bg-red-50 border-red-200",
    label: "Expiré",
  },
  missing: {
    icon: ShieldAlert,
    color: "text-amber-600",
    bg: "bg-amber-50 border-amber-200",
    label: "Manquant",
  },
  unknown: {
    icon: Shield,
    color: "text-slate-500",
    bg: "bg-slate-50 border-slate-200",
    label: "Inconnu",
  },
  mock: {
    icon: Shield,
    color: "text-slate-400",
    bg: "bg-slate-50 border-slate-200",
    label: "Simulé",
  },
};

export function AttestationsCard() {
  const [siret, setSiret] = useState("");
  const [siretToFetch, setSiretToFetch] = useState<string | null>(null);

  const { data, isLoading, error, isFetching } = useQuery<AttestationsData>({
    queryKey: ["attestations", "company", siretToFetch],
    queryFn: () => attestationsApi.checkCompany(siretToFetch!),
    enabled: !!siretToFetch,
    staleTime: 5 * 60 * 1000, // 5 min
    retry: false,
  });

  const handleVerify = () => {
    const cleaned = siret.replace(/\s/g, "");
    if (cleaned.length < 9) return;
    setSiretToFetch(cleaned);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") handleVerify();
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-6">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-9 h-9 bg-primary-50 rounded-xl flex items-center justify-center">
          <Shield className="w-5 h-5 text-primary-600" />
        </div>
        <div>
          <h3 className="font-semibold text-slate-900 text-sm">
            Attestations de conformité
          </h3>
          <p className="text-xs text-slate-400">Via e-Attestations.com</p>
        </div>
      </div>

      {/* SIRET input + bouton vérifier */}
      <div className="flex gap-2 mb-4">
        <input
          type="text"
          value={siret}
          onChange={(e) => setSiret(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="SIRET (ex. 123 456 789 00012)"
          maxLength={17}
          className="flex-1 px-3 py-2 text-sm border border-slate-200 rounded-xl
                     focus:outline-none focus:ring-2 focus:ring-primary-500
                     focus:border-transparent transition-all"
        />
        <button
          onClick={handleVerify}
          disabled={siret.replace(/\s/g, "").length < 9 || isLoading || isFetching}
          className="flex items-center gap-1.5 px-4 py-2 text-sm font-medium
                     bg-primary-50 text-primary-700 rounded-xl
                     hover:bg-primary-100 transition-colors
                     disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading || isFetching ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <RefreshCw className="w-4 h-4" />
          )}
          Vérifier
        </button>
      </div>

      {/* État initial */}
      {!siretToFetch && !data && (
        <div className="text-center py-6 text-slate-400 text-sm">
          <Shield className="w-8 h-8 mx-auto mb-2 text-slate-300" />
          Saisissez votre SIRET et cliquez sur &ldquo;Vérifier&rdquo;
        </div>
      )}

      {/* Erreur */}
      {error && (
        <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700">
          <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
          <div>
            <p className="font-medium">Erreur de vérification</p>
            <p className="text-xs mt-0.5 text-red-500">
              {(error as { message?: string })?.message ||
                "SIRET invalide ou service indisponible"}
            </p>
          </div>
        </div>
      )}

      {/* Résultats */}
      {data && (
        <div className="space-y-2">
          {data.attestations.length === 0 && (
            <p className="text-sm text-slate-400 text-center py-4">
              Aucune attestation trouvée
            </p>
          )}
          {data.attestations.map((att) => {
            const cfg = STATUS_CONFIG[att.status] ?? STATUS_CONFIG.unknown;
            const Icon = cfg.icon;
            return (
              <div
                key={att.type}
                className={`flex items-center justify-between p-3 rounded-xl border ${cfg.bg}`}
              >
                <div className="flex items-center gap-2.5">
                  <Icon className={`w-4 h-4 flex-shrink-0 ${cfg.color}`} />
                  <div>
                    <p className="text-sm font-medium text-slate-800">
                      {TYPE_LABELS[att.type] || att.type}
                    </p>
                    {att.expires_at && (
                      <p className="text-xs text-slate-400">
                        Expire le{" "}
                        {new Date(att.expires_at).toLocaleDateString("fr-FR")}
                      </p>
                    )}
                    {att.is_mock && (
                      <p className="text-xs text-slate-400 italic">
                        Données simulées
                      </p>
                    )}
                  </div>
                </div>
                <span
                  className={`text-xs font-semibold px-2 py-0.5 rounded-full ${cfg.color}`}
                >
                  {cfg.label}
                </span>
              </div>
            );
          })}

          <p className="text-xs text-slate-400 text-right mt-2">
            Vérifié le{" "}
            {new Date(data.checked_at).toLocaleString("fr-FR")}
          </p>
        </div>
      )}
    </div>
  );
}
