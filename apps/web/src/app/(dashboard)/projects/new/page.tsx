"use client";

export const dynamic = "force-dynamic";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import {
  ArrowLeft, Loader2, FileText, Building2,
  Hash, Calendar, ChevronDown, LayoutTemplate, X,
} from "lucide-react";
import Link from "next/link";
import { projectsApi, type ProjectTemplate } from "@/lib/api";
import { useState, useEffect } from "react";
import { cn } from "@/lib/utils";

const schema = z.object({
  title: z.string().min(3, "Titre requis (min 3 caractères)"),
  reference: z.string().optional(),
  buyer: z.string().optional(),
  market_type: z.enum(["travaux", "services", "fournitures"]).optional(),
  submission_deadline: z.string().optional(),
});

type FormData = z.infer<typeof schema>;

function Field({
  label, icon, required, error, children,
}: {
  label: string;
  icon?: React.ReactNode;
  required?: boolean;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label className="flex items-center gap-1.5 text-sm font-medium text-slate-700 mb-1.5">
        {icon && <span className="text-slate-400">{icon}</span>}
        {label}
        {required && <span className="text-danger-500 ml-0.5">*</span>}
      </label>
      {children}
      {error && <p className="text-danger-500 text-xs mt-1">{error}</p>}
    </div>
  );
}

// ── Doc type badge colors ────────────────────────────────────
const DOC_TYPE_COLORS: Record<string, string> = {
  RC:    "bg-primary-100 text-primary-800",
  CCTP:  "bg-blue-100 text-blue-800",
  CCAP:  "bg-success-100 text-success-700",
  DPGF:  "bg-warning-100 text-warning-700",
  BPU:   "bg-purple-100 text-purple-700",
  AE:    "bg-pink-100 text-pink-700",
  ATTRI: "bg-indigo-100 text-indigo-700",
};

export default function NewProjectPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [templates, setTemplates] = useState<ProjectTemplate[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<ProjectTemplate | null>(null);

  const { register, handleSubmit, setValue, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  // Load templates on mount
  useEffect(() => {
    projectsApi.getTemplates()
      .then(r => setTemplates(r.data))
      .catch(() => {/* fail silently — templates are optional */});
  }, []);

  const applyTemplate = (tpl: ProjectTemplate) => {
    setSelectedTemplate(tpl);
    setValue("market_type", tpl.market_type as "travaux" | "services" | "fournitures");
  };

  const clearTemplate = () => {
    setSelectedTemplate(null);
    setValue("market_type", undefined);
  };

  const onSubmit = async (data: FormData) => {
    setLoading(true);
    try {
      const { data: project } = await projectsApi.create({
        ...data,
        submission_deadline: data.submission_deadline
          ? new Date(data.submission_deadline).toISOString()
          : undefined,
      });
      toast.success("Projet créé avec succès !");
      router.push(`/projects/${project.id}`);
    } catch {
      toast.error("Erreur lors de la création du projet");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 md:p-8 max-w-2xl mx-auto animate-fade-in">
      {/* Breadcrumb */}
      <Link
        href="/dashboard"
        className="inline-flex items-center gap-1.5 text-slate-400 text-xs hover:text-primary-700 transition-colors mb-6"
      >
        <ArrowLeft className="w-3 h-3" /> Retour au tableau de bord
      </Link>

      {/* Header */}
      <div className="mb-7">
        <div className="flex items-center gap-3 mb-1">
          <div className="w-10 h-10 bg-primary-50 rounded-xl flex items-center justify-center flex-shrink-0">
            <FileText className="w-5 h-5 text-primary-600" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900">Nouveau projet AO</h1>
            <p className="text-slate-400 text-sm">Renseignez les informations de l&apos;appel d&apos;offres</p>
          </div>
        </div>
      </div>

      {/* ── Template selector (R5) ── */}
      {templates.length > 0 && (
        <div className="mb-5">
          <div className="flex items-center gap-2 mb-3">
            <LayoutTemplate className="w-4 h-4 text-slate-400" />
            <span className="text-sm font-semibold text-slate-700">Partir d&apos;un template</span>
            {selectedTemplate && (
              <button
                onClick={clearTemplate}
                className="ml-auto flex items-center gap-1 text-xs text-slate-400 hover:text-slate-600 transition-colors"
              >
                <X className="w-3 h-3" />
                Projet vierge
              </button>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {templates.map(tpl => (
              <button
                key={tpl.id}
                type="button"
                onClick={() => selectedTemplate?.id === tpl.id ? clearTemplate() : applyTemplate(tpl)}
                className={cn(
                  "text-left p-3.5 rounded-xl border-2 transition-all duration-150",
                  selectedTemplate?.id === tpl.id
                    ? "border-primary-400 bg-primary-50 shadow-sm"
                    : "border-slate-200 hover:border-primary-200 hover:bg-slate-50"
                )}
              >
                <div className="flex items-start gap-2.5">
                  <span className="text-xl leading-none flex-shrink-0 mt-0.5">{tpl.icon}</span>
                  <div className="min-w-0">
                    <p className={cn(
                      "text-sm font-semibold leading-tight mb-0.5",
                      selectedTemplate?.id === tpl.id ? "text-primary-800" : "text-slate-800"
                    )}>
                      {tpl.name}
                    </p>
                    <p className="text-xs text-slate-400 leading-tight mb-2">{tpl.description}</p>
                    <div className="flex flex-wrap gap-1">
                      {tpl.doc_types_expected.map(dt => (
                        <span
                          key={dt}
                          className={cn(
                            "text-[10px] font-bold px-1.5 py-0.5 rounded",
                            DOC_TYPE_COLORS[dt] ?? "bg-slate-100 text-slate-600"
                          )}
                        >
                          {dt}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </button>
            ))}
          </div>

          {!selectedTemplate && (
            <button
              type="button"
              className="mt-2 w-full text-xs text-slate-400 hover:text-slate-600 py-2 border border-dashed border-slate-200 rounded-xl hover:border-slate-300 transition-colors"
              onClick={clearTemplate}
            >
              Continuer sans template (projet vierge)
            </button>
          )}
        </div>
      )}

      {/* Form card */}
      <div className="card p-6 md:p-8">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">

          <Field
            label="Titre du projet"
            icon={<FileText className="w-3.5 h-3.5" />}
            required
            error={errors.title?.message}
          >
            <input
              className="input-field"
              placeholder="Ex : Réhabilitation école Paul Valéry — Lot 2 Gros Œuvre"
              {...register("title")}
            />
          </Field>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Field label="Référence AO" icon={<Hash className="w-3.5 h-3.5" />}>
              <input className="input-field" placeholder="2024-AO-0042" {...register("reference")} />
            </Field>

            <Field label="Type de marché">
              <div className="relative">
                <select className="input-field appearance-none pr-8" {...register("market_type")}>
                  <option value="">Sélectionner…</option>
                  <option value="travaux">Travaux</option>
                  <option value="services">Services</option>
                  <option value="fournitures">Fournitures</option>
                </select>
                <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
              </div>
              {selectedTemplate && (
                <p className="text-xs text-primary-600 mt-1">
                  Pré-rempli par le template &quot;{selectedTemplate.name}&quot;
                </p>
              )}
            </Field>
          </div>

          <Field label="Pouvoir adjudicateur (acheteur)" icon={<Building2 className="w-3.5 h-3.5" />}>
            <input
              className="input-field"
              placeholder="Mairie de Montpellier, Grand Lyon Habitat…"
              {...register("buyer")}
            />
          </Field>

          <Field label="Date limite de remise des offres" icon={<Calendar className="w-3.5 h-3.5" />}>
            <input type="datetime-local" className="input-field text-slate-700" {...register("submission_deadline")} />
          </Field>

          <div className="h-px bg-slate-100" />

          <div className="flex items-center justify-between gap-3">
            <Link href="/dashboard" className="btn-secondary text-sm">
              Annuler
            </Link>
            <button type="submit" disabled={loading} className="btn-primary-gradient flex items-center gap-2">
              {loading
                ? <><Loader2 className="w-4 h-4 animate-spin" /> Création…</>
                : <><FileText className="w-4 h-4" /> Créer le projet</>
              }
            </button>
          </div>
        </form>
      </div>

      <div className="mt-4 bg-primary-50 border border-primary-100 rounded-xl px-4 py-3">
        <p className="text-xs text-primary-700 leading-relaxed">
          <strong>Prochaine étape :</strong> Après la création, importez vos PDFs (RC, CCTP, CCAP, DPGF…)
          et lancez l&apos;analyse IA pour obtenir un résumé complet en 3–5 minutes.
        </p>
      </div>
    </div>
  );
}
