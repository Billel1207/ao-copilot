"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/auth";
import { projectsApi } from "@/lib/api";
import {
  Building2, HardHat, Wrench, Briefcase,
  ArrowRight, CheckCircle2, Loader2, X,
  FileText, Sparkles, Users2
} from "lucide-react";
import { cn } from "@/lib/utils";

const STORAGE_KEY = "ao_onboarding_done";

// ── Step types ────────────────────────────────────────────────────────────

type Sector = "btp_gros_oeuvre" | "btp_second_oeuvre" | "ingenierie" | "services" | "autre";
type Size   = "1" | "2-10" | "11-50" | "51-200" | "200+";

interface OnboardingData {
  sector: Sector | null;
  size: Size | null;
  projectName: string;
}

// ── Sector options ────────────────────────────────────────────────────────

const SECTORS: { value: Sector; label: string; icon: React.ElementType; desc: string }[] = [
  { value: "btp_gros_oeuvre",   label: "BTP — Gros Œuvre",      icon: HardHat,   desc: "Structure, béton, maçonnerie" },
  { value: "btp_second_oeuvre", label: "BTP — Second Œuvre",    icon: Wrench,    desc: "Menuiserie, électricité, plomberie…" },
  { value: "ingenierie",        label: "Ingénierie / Bureaux",   icon: Building2, desc: "MOE, OPC, études techniques" },
  { value: "services",          label: "Services & Fournitures", icon: Briefcase, desc: "Prestations, maintenance, SaaS" },
];

const SIZES: { value: Size; label: string }[] = [
  { value: "1",       label: "Auto-entrepreneur" },
  { value: "2-10",    label: "2–10 salariés" },
  { value: "11-50",   label: "11–50 salariés" },
  { value: "51-200",  label: "51–200 salariés" },
  { value: "200+",    label: "200+ salariés" },
];

// ── Progress dots ─────────────────────────────────────────────────────────

function StepDots({ current, total }: { current: number; total: number }) {
  return (
    <div className="flex items-center gap-2">
      {Array.from({ length: total }).map((_, i) => (
        <div
          key={i}
          className={cn(
            "rounded-full transition-all duration-300",
            i === current
              ? "w-6 h-2 bg-primary-600"
              : i < current
              ? "w-2 h-2 bg-primary-300"
              : "w-2 h-2 bg-slate-200"
          )}
        />
      ))}
    </div>
  );
}

// ── Step 1: Profil entreprise ─────────────────────────────────────────────

function Step1({
  data, onChange, onNext,
}: {
  data: OnboardingData;
  onChange: (d: Partial<OnboardingData>) => void;
  onNext: () => void;
}) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-slate-900">Bienvenue sur AO Copilot !</h2>
        <p className="text-sm text-slate-500 mt-1">
          En 2 minutes, configurons votre espace pour une expérience personnalisée.
        </p>
      </div>

      {/* Sector */}
      <div>
        <p className="text-sm font-semibold text-slate-700 mb-2.5">
          Votre secteur d&apos;activité *
        </p>
        <div className="grid grid-cols-2 gap-2">
          {SECTORS.map(s => (
            <button
              key={s.value}
              onClick={() => onChange({ sector: s.value })}
              className={cn(
                "flex items-start gap-2.5 p-3 rounded-xl border-2 text-left transition-all duration-150",
                data.sector === s.value
                  ? "border-primary-500 bg-primary-50"
                  : "border-slate-200 hover:border-slate-300 hover:bg-slate-50"
              )}
            >
              <s.icon className={cn(
                "w-4 h-4 mt-0.5 flex-shrink-0",
                data.sector === s.value ? "text-primary-600" : "text-slate-400"
              )} />
              <div>
                <p className={cn(
                  "text-xs font-semibold leading-tight",
                  data.sector === s.value ? "text-primary-800" : "text-slate-700"
                )}>
                  {s.label}
                </p>
                <p className="text-[10px] text-slate-400 mt-0.5 leading-tight">{s.desc}</p>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Size */}
      <div>
        <p className="text-sm font-semibold text-slate-700 mb-2.5">Taille de votre entreprise *</p>
        <div className="flex flex-wrap gap-2">
          {SIZES.map(s => (
            <button
              key={s.value}
              onClick={() => onChange({ size: s.value })}
              className={cn(
                "px-3 py-1.5 rounded-full text-xs font-medium border-2 transition-all duration-150",
                data.size === s.value
                  ? "border-primary-500 bg-primary-50 text-primary-700"
                  : "border-slate-200 text-slate-600 hover:border-slate-300"
              )}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      <button
        onClick={onNext}
        disabled={!data.sector || !data.size}
        className="w-full flex items-center justify-center gap-2 py-3 px-4 bg-primary-700 hover:bg-primary-800 disabled:bg-slate-200 disabled:text-slate-400 text-white rounded-xl font-semibold text-sm transition-all duration-150"
      >
        Continuer
        <ArrowRight className="w-4 h-4" />
      </button>
    </div>
  );
}

// ── Step 2: Premier projet ────────────────────────────────────────────────

function Step2({
  data, onChange, onNext, onSkip, isCreating,
}: {
  data: OnboardingData;
  onChange: (d: Partial<OnboardingData>) => void;
  onNext: () => void;
  onSkip: () => void;
  isCreating: boolean;
}) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-slate-900">Votre premier appel d&apos;offres</h2>
        <p className="text-sm text-slate-500 mt-1">
          Créez un projet pour organiser vos documents DCE et obtenir une analyse IA.
        </p>
      </div>

      <div className="bg-primary-50 border border-primary-100 rounded-xl p-4">
        <div className="flex items-start gap-3">
          <Sparkles className="w-5 h-5 text-primary-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-semibold text-primary-800">Ce que vous obtiendrez</p>
            <ul className="text-xs text-primary-700 mt-1 space-y-0.5">
              <li>• Résumé exécutif du DCE en 30 secondes</li>
              <li>• Checklist des documents à fournir</li>
              <li>• Score Go / No-Go stratégique</li>
              <li>• Timeline et dates clés extraites</li>
            </ul>
          </div>
        </div>
      </div>

      <div>
        <label className="block text-sm font-semibold text-slate-700 mb-1.5">
          Nom du projet / marché
        </label>
        <input
          type="text"
          value={data.projectName}
          onChange={e => onChange({ projectName: e.target.value })}
          placeholder="Ex : Rénovation école Jean-Moulin — Lot 2"
          className="w-full px-3 py-2.5 border border-slate-200 rounded-xl text-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition"
          onKeyDown={e => e.key === "Enter" && data.projectName.trim() && onNext()}
          autoFocus
        />
        <p className="text-[11px] text-slate-400 mt-1">Vous pourrez le modifier plus tard</p>
      </div>

      <div className="flex gap-3">
        <button
          onClick={onSkip}
          className="flex-1 py-3 px-4 border border-slate-200 text-slate-600 rounded-xl font-medium text-sm hover:bg-slate-50 transition"
        >
          Passer cette étape
        </button>
        <button
          onClick={onNext}
          disabled={!data.projectName.trim() || isCreating}
          className="flex-1 flex items-center justify-center gap-2 py-3 px-4 bg-primary-700 hover:bg-primary-800 disabled:bg-slate-200 disabled:text-slate-400 text-white rounded-xl font-semibold text-sm transition-all duration-150"
        >
          {isCreating ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Création…
            </>
          ) : (
            <>
              Créer le projet
              <ArrowRight className="w-4 h-4" />
            </>
          )}
        </button>
      </div>
    </div>
  );
}

// ── Step 3: Success ───────────────────────────────────────────────────────

function Step3({
  projectId, onClose,
}: {
  projectId: string | null;
  onClose: (goToProject?: boolean) => void;
}) {
  const router = useRouter();

  return (
    <div className="space-y-6 text-center">
      <div className="flex justify-center">
        <div className="w-20 h-20 rounded-full bg-success-50 flex items-center justify-center animate-scale-in">
          <CheckCircle2 className="w-10 h-10 text-success-600" />
        </div>
      </div>

      <div>
        <h2 className="text-xl font-bold text-slate-900">Tout est prêt !</h2>
        <p className="text-sm text-slate-500 mt-2">
          Votre espace AO Copilot est configuré.
          {projectId && " Uploadez vos documents DCE pour lancer l'analyse IA."}
        </p>
      </div>

      {/* Features grid */}
      <div className="grid grid-cols-3 gap-3 text-center">
        {[
          { icon: FileText, label: "Upload PDFs", desc: "Tous formats" },
          { icon: Sparkles, label: "Analyse IA",  desc: "30 secondes" },
          { icon: Users2,   label: "Équipe",      desc: "Collaborez" },
        ].map(f => (
          <div key={f.label} className="p-3 bg-slate-50 rounded-xl">
            <f.icon className="w-5 h-5 text-primary-600 mx-auto mb-1" />
            <p className="text-xs font-semibold text-slate-700">{f.label}</p>
            <p className="text-[10px] text-slate-400">{f.desc}</p>
          </div>
        ))}
      </div>

      <div className="flex flex-col gap-2.5">
        {projectId && (
          <button
            onClick={() => {
              onClose();
              router.push(`/projects/${projectId}/upload`);
            }}
            className="w-full flex items-center justify-center gap-2 py-3 px-4 bg-primary-700 hover:bg-primary-800 text-white rounded-xl font-semibold text-sm transition"
          >
            <FileText className="w-4 h-4" />
            Uploader mon DCE maintenant
          </button>
        )}
        <button
          onClick={() => onClose()}
          className="w-full py-2.5 px-4 text-slate-500 text-sm hover:text-slate-700 transition"
        >
          Aller au tableau de bord
        </button>
      </div>
    </div>
  );
}

// ── Main Modal ────────────────────────────────────────────────────────────

export function OnboardingModal() {
  const { user, isAuthenticated } = useAuthStore();
  const [open, setOpen] = useState(false);
  const [step, setStep] = useState(0);
  const [isCreating, setIsCreating] = useState(false);
  const [createdProjectId, setCreatedProjectId] = useState<string | null>(null);
  const [data, setData] = useState<OnboardingData>({
    sector: null,
    size: null,
    projectName: "",
  });

  // Show only for authenticated users who haven't completed onboarding
  useEffect(() => {
    if (isAuthenticated && user) {
      const done = localStorage.getItem(STORAGE_KEY);
      if (!done) {
        // Small delay so layout renders first
        setTimeout(() => setOpen(true), 600);
      }
    }
  }, [isAuthenticated, user]);

  const handleChange = (patch: Partial<OnboardingData>) =>
    setData(prev => ({ ...prev, ...patch }));

  const handleStep1Next = () => setStep(1);

  const handleStep2Next = async () => {
    if (!data.projectName.trim()) return;
    setIsCreating(true);
    try {
      const { data: proj } = await projectsApi.create({ title: data.projectName.trim() });
      setCreatedProjectId(proj.id);
    } catch {
      // Non-blocking — continue to success step
    } finally {
      setIsCreating(false);
      setStep(2);
    }
  };

  const handleSkip = () => setStep(2);

  const handleClose = () => {
    localStorage.setItem(STORAGE_KEY, "1");
    setOpen(false);
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm" />

      {/* Modal */}
      <div className="relative w-full max-w-md bg-white rounded-2xl shadow-elevation animate-slide-up">

        {/* Header bar */}
        <div className="flex items-center justify-between px-6 pt-5 pb-4 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-gradient-to-br from-primary-700 to-primary-900 rounded-md flex items-center justify-center">
              <span className="text-white font-bold text-[10px]">AO</span>
            </div>
            <span className="text-sm font-bold text-primary-900">Configuration initiale</span>
          </div>
          <div className="flex items-center gap-3">
            <StepDots current={step} total={3} />
            {step < 2 && (
              <button
                onClick={handleClose}
                className="text-slate-400 hover:text-slate-600 transition"
                aria-label="Fermer"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        {/* Content */}
        <div className="px-6 py-5">
          {step === 0 && (
            <Step1 data={data} onChange={handleChange} onNext={handleStep1Next} />
          )}
          {step === 1 && (
            <Step2
              data={data}
              onChange={handleChange}
              onNext={handleStep2Next}
              onSkip={handleSkip}
              isCreating={isCreating}
            />
          )}
          {step === 2 && (
            <Step3 projectId={createdProjectId} onClose={handleClose} />
          )}
        </div>
      </div>
    </div>
  );
}
