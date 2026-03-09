"use client";
import { useState, useEffect } from "react";
import {
  Building2, Save, Loader2, CheckCircle2, AlertCircle,
  Euro, Users, Award, MapPin, BarChart3
} from "lucide-react";
import { toast } from "sonner";
import { useCompanyProfile, useUpdateCompanyProfile } from "@/hooks/useAnalysis";
import { AttestationsCard } from "@/components/attestations/AttestationsCard";

// ── Constants ─────────────────────────────────────────────────────────────

const CERTIFICATIONS = [
  { id: "Qualibat", label: "Qualibat" },
  { id: "ISO9001", label: "ISO 9001" },
  { id: "MASE", label: "MASE" },
  { id: "RGE", label: "RGE (Reconnu Garant de l'Environnement)" },
  { id: "OPQIBI", label: "OPQIBI (Ingénierie)" },
  { id: "ISO14001", label: "ISO 14001" },
  { id: "OHSAS18001", label: "OHSAS 18001 / ISO 45001" },
  { id: "QualiPV", label: "QualiPV" },
  { id: "Qualifelec", label: "Qualifelec" },
  { id: "AFNOR", label: "Certification AFNOR" },
  { id: "CE", label: "Marquage CE" },
];

const SPECIALTIES = [
  { id: "gros_oeuvre", label: "Gros-oeuvre / Maçonnerie" },
  { id: "charpente_couverture", label: "Charpente / Couverture" },
  { id: "electricite", label: "Electricité / CFO-CFA" },
  { id: "plomberie_sanitaire", label: "Plomberie / Sanitaire" },
  { id: "chauffage_climatisation", label: "Chauffage / Climatisation (CVC)" },
  { id: "menuiserie", label: "Menuiserie / Serrurerie" },
  { id: "peinture_revetement", label: "Peinture / Revêtements" },
  { id: "vrd", label: "VRD / Terrassement" },
  { id: "demolition", label: "Démolition / Désamiantage" },
  { id: "structure_metallique", label: "Structures métalliques" },
  { id: "etancheite", label: "Etanchéité / Isolation" },
  { id: "ingenierie_bureau_etudes", label: "Ingénierie / Bureau d'études" },
  { id: "moe_maitrise_oeuvre", label: "Maîtrise d'oeuvre" },
  { id: "amenagement_interieur", label: "Aménagement intérieur" },
  { id: "ascenseur_levage", label: "Ascenseurs / Levage" },
  { id: "espaces_verts", label: "Espaces verts / Paysage" },
  { id: "nettoyage_gardiennage", label: "Nettoyage / Gardiennage" },
  { id: "numerique_it", label: "Numérique / Informatique" },
];

const REGIONS_FRANCE = [
  "Île-de-France",
  "Auvergne-Rhône-Alpes",
  "Nouvelle-Aquitaine",
  "Occitanie",
  "Hauts-de-France",
  "Grand Est",
  "Provence-Alpes-Côte d'Azur",
  "Pays de la Loire",
  "Normandie",
  "Bretagne",
  "Bourgogne-Franche-Comté",
  "Centre-Val de Loire",
  "Corse",
  "Guadeloupe",
  "Martinique",
  "Guyane",
  "La Réunion",
  "Mayotte",
  "National (toute France)",
];

// ── Form state type ────────────────────────────────────────────────────────

interface FormState {
  revenue_eur: string;
  employee_count: string;
  max_market_size_eur: string;
  certifications: string[];
  specialties: string[];
  regions: string[];
}

// ── Checkbox group ─────────────────────────────────────────────────────────

function CheckboxGroup({
  items,
  selected,
  onChange,
  cols = 2,
}: {
  items: { id: string; label: string }[];
  selected: string[];
  onChange: (updated: string[]) => void;
  cols?: number;
}) {
  const toggle = (id: string) => {
    if (selected.includes(id)) {
      onChange(selected.filter((s) => s !== id));
    } else {
      onChange([...selected, id]);
    }
  };

  return (
    <div className={`grid grid-cols-1 sm:grid-cols-${cols} gap-2`}>
      {items.map((item) => {
        const checked = selected.includes(item.id);
        return (
          <label
            key={item.id}
            className={`flex items-center gap-2.5 p-3 rounded-xl border cursor-pointer
                        transition-all duration-150 select-none
                        ${checked
                          ? "bg-primary-50 border-primary-300 text-primary-800"
                          : "bg-white border-slate-100 text-slate-700 hover:border-primary-200 hover:bg-primary-50/30"
                        }`}
          >
            <input
              type="checkbox"
              checked={checked}
              onChange={() => toggle(item.id)}
              className="w-4 h-4 accent-primary-600 flex-shrink-0"
            />
            <span className="text-sm font-medium">{item.label}</span>
          </label>
        );
      })}
    </div>
  );
}

// ── Section wrapper ────────────────────────────────────────────────────────

function Section({
  icon,
  title,
  description,
  children,
}: {
  icon: React.ReactNode;
  title: string;
  description?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="card p-6">
      <div className="flex items-start gap-3 mb-5">
        <div className="w-8 h-8 rounded-lg bg-primary-50 flex items-center justify-center flex-shrink-0">
          {icon}
        </div>
        <div>
          <h2 className="text-sm font-semibold text-slate-800">{title}</h2>
          {description && (
            <p className="text-xs text-slate-400 mt-0.5">{description}</p>
          )}
        </div>
      </div>
      {children}
    </div>
  );
}

// ── Number input ─────────────────────────────────────────────────────────

function NumberInput({
  label,
  value,
  onChange,
  placeholder,
  suffix,
  hint,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  suffix?: string;
  hint?: string;
}) {
  return (
    <div>
      <label className="block text-xs font-semibold text-slate-600 mb-1.5">
        {label}
      </label>
      <div className="relative">
        <input
          type="number"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          min={0}
          className="w-full px-3 py-2 text-sm border border-slate-200 rounded-xl
                     focus:outline-none focus:ring-2 focus:ring-primary-500
                     focus:border-transparent transition-all pr-16"
        />
        {suffix && (
          <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-slate-400 font-medium pointer-events-none">
            {suffix}
          </span>
        )}
      </div>
      {hint && <p className="text-[10px] text-slate-400 mt-1">{hint}</p>}
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────

export default function CompanyProfilePage() {
  const { data: profile, isLoading, error } = useCompanyProfile();
  const updateProfile = useUpdateCompanyProfile();

  const [form, setForm] = useState<FormState>({
    revenue_eur: "",
    employee_count: "",
    max_market_size_eur: "",
    certifications: [],
    specialties: [],
    regions: [],
  });

  // Sync form when profile loads
  useEffect(() => {
    if (profile) {
      setForm({
        revenue_eur: profile.revenue_eur != null ? String(profile.revenue_eur) : "",
        employee_count: profile.employee_count != null ? String(profile.employee_count) : "",
        max_market_size_eur:
          profile.max_market_size_eur != null ? String(profile.max_market_size_eur) : "",
        certifications: profile.certifications ?? [],
        specialties: profile.specialties ?? [],
        regions: profile.regions ?? [],
      });
    }
  }, [profile]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const payload = {
      revenue_eur: form.revenue_eur ? parseInt(form.revenue_eur, 10) : null,
      employee_count: form.employee_count ? parseInt(form.employee_count, 10) : null,
      max_market_size_eur: form.max_market_size_eur
        ? parseInt(form.max_market_size_eur, 10)
        : null,
      certifications: form.certifications,
      specialties: form.specialties,
      regions: form.regions,
    };

    updateProfile.mutate(payload, {
      onSuccess: () => {
        toast.success("Profil entreprise enregistré avec succès");
      },
      onError: (err: Error) => {
        toast.error(err.message || "Erreur lors de la sauvegarde");
      },
    });
  };

  if (isLoading) {
    return (
      <div className="p-6 md:p-8 max-w-4xl mx-auto">
        <div className="flex items-center gap-2 text-slate-400 text-sm">
          <Loader2 className="w-4 h-4 animate-spin" />
          Chargement du profil...
        </div>
      </div>
    );
  }

  if (error && (error as { response?: { status?: number } }).response?.status !== 404) {
    return (
      <div className="p-6 md:p-8 max-w-4xl mx-auto">
        <div className="card p-6 text-center text-danger-600">
          <AlertCircle className="w-5 h-5 mx-auto mb-2" />
          Erreur lors du chargement du profil entreprise.
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 md:p-8 max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
          <Building2 className="w-5 h-5 text-primary-600" />
          Profil entreprise
        </h1>
        <p className="text-slate-500 text-sm mt-1">
          Ces informations enrichissent automatiquement le score Go/No-Go en comparant
          votre profil aux exigences de chaque marché.
        </p>
      </div>

      {!profile && (
        <div className="mb-6 p-4 rounded-xl border border-amber-200 bg-amber-50 flex items-start gap-3">
          <AlertCircle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-amber-800">
            Aucun profil configuré. Remplissez le formulaire ci-dessous pour activer le
            Go/No-Go enrichi.
          </p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">

        {/* ── Informations financières ── */}
        <Section
          icon={<Euro className="w-4 h-4 text-primary-600" />}
          title="Informations financières"
          description="Utilisées pour vérifier l'adéquation CA / taille du marché"
        >
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <NumberInput
              label="Chiffre d'affaires annuel (€)"
              value={form.revenue_eur}
              onChange={(v) => setForm((f) => ({ ...f, revenue_eur: v }))}
              placeholder="ex. 2500000"
              suffix="€/an"
              hint="Dernier exercice fiscal"
            />
            <NumberInput
              label="Taille max du marché gérable (€)"
              value={form.max_market_size_eur}
              onChange={(v) => setForm((f) => ({ ...f, max_market_size_eur: v }))}
              placeholder="ex. 5000000"
              suffix="€"
              hint="Montant maximum d'un marché que vous pouvez répondre"
            />
          </div>
        </Section>

        {/* ── Effectifs ── */}
        <Section
          icon={<Users className="w-4 h-4 text-primary-600" />}
          title="Effectifs"
        >
          <div className="max-w-xs">
            <NumberInput
              label="Nombre de salariés"
              value={form.employee_count}
              onChange={(v) => setForm((f) => ({ ...f, employee_count: v }))}
              placeholder="ex. 45"
              suffix="ETP"
              hint="Equivalent temps plein (ETP)"
            />
          </div>
        </Section>

        {/* ── Certifications ── */}
        <Section
          icon={<Award className="w-4 h-4 text-primary-600" />}
          title="Certifications & qualifications"
          description="Cochez toutes vos certifications valides"
        >
          <CheckboxGroup
            items={CERTIFICATIONS}
            selected={form.certifications}
            onChange={(v) => setForm((f) => ({ ...f, certifications: v }))}
          />
        </Section>

        {/* ── Spécialités ── */}
        <Section
          icon={<BarChart3 className="w-4 h-4 text-primary-600" />}
          title="Domaines d'activité"
          description="Vos métiers principaux dans le BTP"
        >
          <CheckboxGroup
            items={SPECIALTIES}
            selected={form.specialties}
            onChange={(v) => setForm((f) => ({ ...f, specialties: v }))}
          />
        </Section>

        {/* ── Régions ── */}
        <Section
          icon={<MapPin className="w-4 h-4 text-primary-600" />}
          title="Régions d'intervention"
          description="Zones géographiques où vous répondez à des marchés"
        >
          <CheckboxGroup
            items={REGIONS_FRANCE.map((r) => ({ id: r, label: r }))}
            selected={form.regions}
            onChange={(v) => setForm((f) => ({ ...f, regions: v }))}
            cols={2}
          />
        </Section>

        {/* ── Submit ── */}
        <div className="flex items-center justify-between pt-2">
          <p className="text-xs text-slate-400">
            {form.certifications.length} certification(s) · {form.specialties.length} spécialité(s) · {form.regions.length} région(s)
          </p>
          <button
            type="submit"
            disabled={updateProfile.isPending}
            className="btn-primary-gradient flex items-center gap-2 px-6"
          >
            {updateProfile.isPending ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Enregistrement...
              </>
            ) : (
              <>
                <Save className="w-4 h-4" />
                Enregistrer le profil
              </>
            )}
          </button>
        </div>

        {updateProfile.isSuccess && (
          <div className="flex items-center gap-2 text-sm text-success-700 bg-success-50 border border-success-200 rounded-xl px-4 py-3">
            <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
            Profil enregistré — le Go/No-Go sera enrichi lors de la prochaine analyse.
          </div>
        )}
      </form>

      {/* ── Attestations de conformité ── */}
      <div className="mt-6">
        <AttestationsCard />
      </div>
    </div>
  );
}
