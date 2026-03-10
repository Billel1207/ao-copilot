"use client";

export const dynamic = "force-dynamic";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Building2, Settings, Rocket, ChevronRight, ChevronLeft, Check, Loader2 } from "lucide-react";
import { apiClient } from "@/lib/api";

// 3 étapes
const STEPS = [
  { id: 1, title: "Votre entreprise", description: "Parlez-nous de votre activité", icon: Building2 },
  { id: 2, title: "Vos préférences", description: "Configurez vos alertes", icon: Settings },
  { id: 3, title: "C'est parti !", description: "Tout est prêt", icon: Rocket },
];

const SECTORS = [
  { value: "gros_oeuvre", label: "Gros Œuvre" },
  { value: "second_oeuvre", label: "Second Œuvre" },
  { value: "vrd", label: "VRD / Espaces verts" },
  { value: "ingenierie", label: "Ingénierie / Bureau d'études" },
  { value: "autre", label: "Autre" },
];

const REGIONS = [
  "Île-de-France",
  "Auvergne-Rhône-Alpes",
  "Provence-Alpes-Côte d'Azur",
  "Occitanie",
  "Hauts-de-France",
  "Nouvelle-Aquitaine",
  "Grand Est",
  "Bretagne",
  "Normandie",
  "Pays de la Loire",
  "Bourgogne-Franche-Comté",
  "Centre-Val de Loire",
  "PACA",
  "Corse",
  "DOM-TOM",
];

const DOC_TYPES = [
  { value: "RC", label: "Règlement de Consultation" },
  { value: "CCTP", label: "Cahier des Clauses Techniques" },
  { value: "CCAP", label: "Cahier des Clauses Administratives" },
  { value: "DPGF", label: "DPGF / BPU" },
  { value: "ATTRI", label: "Lettre d'attribution" },
];

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);

  // Step 1 state
  const [siret, setSiret] = useState("");
  const [sector, setSector] = useState("");
  const [selectedRegions, setSelectedRegions] = useState<string[]>([]);

  // Step 2 state
  const [selectedDocTypes, setSelectedDocTypes] = useState<string[]>(["RC", "CCTP", "CCAP"]);
  const [notifyAnalysis, setNotifyAnalysis] = useState(true);
  const [notifyDeadline, setNotifyDeadline] = useState(true);
  const [notifyQuota, setNotifyQuota] = useState(true);

  const toggleRegion = (r: string) => {
    setSelectedRegions(prev => prev.includes(r) ? prev.filter(x => x !== r) : [...prev, r]);
  };
  const toggleDocType = (d: string) => {
    setSelectedDocTypes(prev => prev.includes(d) ? prev.filter(x => x !== d) : [...prev, d]);
  };

  const handleComplete = async () => {
    setIsLoading(true);
    try {
      await apiClient.post("/api/v1/onboarding/complete", {
        step1: { siret, sector, regions: selectedRegions },
        step2: {
          doc_types: selectedDocTypes,
          notify_analysis: notifyAnalysis,
          notify_deadline: notifyDeadline,
          notify_quota: notifyQuota,
        },
      });
      toast.success("Bienvenue sur AO Copilot !");
      router.push("/dashboard");
    } catch {
      toast.error("Erreur lors de la sauvegarde.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center p-4">
      <div className="w-full max-w-2xl">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-2 mb-4">
            <div className="w-10 h-10 bg-primary-600 rounded-xl flex items-center justify-center">
              <span className="text-white font-bold">AO</span>
            </div>
            <span className="text-xl font-bold text-slate-800">AO Copilot</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 mb-1">Configuration de votre compte</h1>
          <p className="text-slate-500 text-sm">3 étapes rapides pour personnaliser votre expérience</p>
        </div>

        {/* Stepper */}
        <div className="flex items-center justify-center gap-2 mb-8">
          {STEPS.map((s, i) => (
            <div key={s.id} className="flex items-center gap-2">
              <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium transition-all ${
                step === s.id ? "bg-primary-600 text-white" :
                step > s.id ? "bg-success-100 text-success-700" : "bg-slate-100 text-slate-400"
              }`}>
                {step > s.id ? <Check className="w-3.5 h-3.5" /> : <s.icon className="w-3.5 h-3.5" />}
                <span className="hidden sm:inline">{s.title}</span>
                <span className="sm:hidden">{s.id}</span>
              </div>
              {i < STEPS.length - 1 && (
                <div className={`w-8 h-0.5 rounded ${step > s.id ? "bg-success-300" : "bg-slate-200"}`} />
              )}
            </div>
          ))}
        </div>

        {/* Card */}
        <div className="bg-white rounded-2xl shadow-lg border border-slate-100 p-8">
          {/* Step 1 */}
          {step === 1 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-lg font-bold text-slate-900 mb-1 flex items-center gap-2">
                  <Building2 className="w-5 h-5 text-primary-600" />
                  Parlez-nous de votre entreprise
                </h2>
                <p className="text-slate-500 text-sm">Ces informations nous permettent d&apos;affiner l&apos;analyse IA.</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">SIRET (optionnel)</label>
                <input
                  value={siret}
                  onChange={e => setSiret(e.target.value)}
                  placeholder="123 456 789 00000"
                  className="w-full px-3 py-2.5 text-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Votre secteur d&apos;activité</label>
                <div className="grid grid-cols-2 gap-2">
                  {SECTORS.map(s => (
                    <button
                      key={s.value}
                      type="button"
                      onClick={() => setSector(s.value)}
                      className={`px-3 py-2.5 text-sm rounded-xl border text-left transition-all ${
                        sector === s.value
                          ? "bg-primary-50 border-primary-400 text-primary-700 font-medium"
                          : "border-slate-200 text-slate-600 hover:border-primary-300"
                      }`}
                    >
                      {s.label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Régions d&apos;intervention <span className="text-slate-400 font-normal">(plusieurs possibles)</span>
                </label>
                <div className="flex flex-wrap gap-2">
                  {REGIONS.map(r => (
                    <button
                      key={r}
                      type="button"
                      onClick={() => toggleRegion(r)}
                      className={`px-3 py-1 text-xs rounded-full border transition-all ${
                        selectedRegions.includes(r)
                          ? "bg-primary-100 border-primary-400 text-primary-700"
                          : "border-slate-200 text-slate-500 hover:border-primary-300"
                      }`}
                    >
                      {r}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Step 2 */}
          {step === 2 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-lg font-bold text-slate-900 mb-1 flex items-center gap-2">
                  <Settings className="w-5 h-5 text-primary-600" />
                  Vos préférences d&apos;analyse
                </h2>
                <p className="text-slate-500 text-sm">Configurez les alertes et types de documents prioritaires.</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Types de documents analysés en priorité
                </label>
                <div className="space-y-2">
                  {DOC_TYPES.map(d => (
                    <label key={d.value} className="flex items-center gap-3 cursor-pointer group">
                      <input
                        type="checkbox"
                        checked={selectedDocTypes.includes(d.value)}
                        onChange={() => toggleDocType(d.value)}
                        className="w-4 h-4 rounded border-slate-300 text-primary-600 focus:ring-primary-500"
                      />
                      <span className="text-sm text-slate-700 group-hover:text-slate-900">
                        <span className="font-mono text-xs bg-slate-100 px-1.5 py-0.5 rounded mr-2">{d.value}</span>
                        {d.label}
                      </span>
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-3">Notifications email</label>
                <div className="space-y-3">
                  {[
                    { key: "analysis", state: notifyAnalysis, set: setNotifyAnalysis, label: "Analyse IA terminée", desc: "Reçevez un email dès que votre DCE est analysé" },
                    { key: "deadline", state: notifyDeadline, set: setNotifyDeadline, label: "Rappels de deadlines (J-7)", desc: "Alerte 7 jours avant chaque date limite" },
                    { key: "quota", state: notifyQuota, set: setNotifyQuota, label: "Alerte quota documents", desc: "Avertissement à 80% du quota mensuel" },
                  ].map(({ key, state, set, label, desc }) => (
                    <label key={key} className="flex items-start gap-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={state}
                        onChange={e => set(e.target.checked)}
                        className="w-4 h-4 rounded border-slate-300 text-primary-600 focus:ring-primary-500 mt-0.5"
                      />
                      <div>
                        <p className="text-sm font-medium text-slate-700">{label}</p>
                        <p className="text-xs text-slate-400">{desc}</p>
                      </div>
                    </label>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Step 3 */}
          {step === 3 && (
            <div className="text-center space-y-6">
              <div className="w-20 h-20 bg-success-50 rounded-full flex items-center justify-center mx-auto">
                <Rocket className="w-10 h-10 text-success-600" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-slate-900 mb-2">Tout est prêt !</h2>
                <p className="text-slate-500 text-sm max-w-sm mx-auto">
                  Votre compte AO Copilot est configuré. Commencez par créer votre premier projet AO.
                </p>
              </div>

              <div className="bg-slate-50 rounded-xl p-5 text-left space-y-3">
                <p className="text-sm font-semibold text-slate-700 mb-3">Ce qui vous attend :</p>
                {[
                  { icon: "📄", text: "Importez vos documents DCE (RC, CCTP, CCAP, DPGF...)" },
                  { icon: "🤖", text: "L'IA génère une checklist de conformité en 5 min" },
                  { icon: "📊", text: "Score Go/No-Go + Mémoire Technique automatique" },
                  { icon: "📅", text: "Alertes deadlines + Veille BOAMP" },
                ].map(({ icon, text }) => (
                  <div key={text} className="flex items-center gap-3 text-sm text-slate-600">
                    <span>{icon}</span>
                    <span>{text}</span>
                  </div>
                ))}
              </div>

              <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-sm text-amber-700">
                <strong>Essai gratuit 14 jours</strong> — Pas de carte bancaire requise.
                5 analyses gratuites incluses.
              </div>
            </div>
          )}

          {/* Navigation */}
          <div className="flex items-center justify-between mt-8 pt-6 border-t border-slate-100">
            <button
              type="button"
              onClick={() => step > 1 && setStep(step - 1)}
              className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-xl transition-all ${
                step === 1 ? "invisible" : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              <ChevronLeft className="w-4 h-4" />
              Précédent
            </button>

            <span className="text-xs text-slate-400">{step} / {STEPS.length}</span>

            {step < STEPS.length ? (
              <button
                type="button"
                onClick={() => setStep(step + 1)}
                className="btn-primary-gradient flex items-center gap-2 px-5 py-2 text-sm"
              >
                Suivant
                <ChevronRight className="w-4 h-4" />
              </button>
            ) : (
              <button
                type="button"
                onClick={handleComplete}
                disabled={isLoading}
                className="btn-primary-gradient flex items-center gap-2 px-5 py-2 text-sm"
              >
                {isLoading && <Loader2 className="w-4 h-4 animate-spin" />}
                Commencer
                <Rocket className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        {/* Skip */}
        <p className="text-center mt-4">
          <button
            type="button"
            onClick={handleComplete}
            className="text-xs text-slate-400 hover:text-slate-600 underline"
          >
            Passer cette étape
          </button>
        </p>
      </div>
    </div>
  );
}
