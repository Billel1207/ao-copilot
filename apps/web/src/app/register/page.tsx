"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { Loader2, FileCheck2, ShieldCheck, TrendingUp } from "lucide-react";
import { useAuthStore } from "@/stores/auth";

const schema = z.object({
  full_name: z.string().min(2, "Nom requis (2 caractères minimum)"),
  org_name:  z.string().min(2, "Nom entreprise requis"),
  email:     z.string().email("Email invalide"),
  password:  z.string().min(8, "8 caractères minimum"),
});

type FormData = z.infer<typeof schema>;

const FEATURES = [
  { icon: FileCheck2,  text: "Analyse complète RC, CCTP, CCAP, DPGF en 3 minutes" },
  { icon: ShieldCheck, text: "Détection automatique des risques éliminatoires" },
  { icon: TrendingUp,  text: "Score d'éligibilité et actions à prendre sous 48h" },
];

export default function RegisterPage() {
  const router = useRouter();
  const { register: registerUser, isLoading, error, clearError } = useAuthStore();
  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (data: FormData) => {
    clearError();
    try {
      await registerUser(data);
      router.push("/onboarding");
      toast.success("Compte créé avec succès !");
    } catch {
      toast.error("Une erreur est survenue. Cet email est peut-être déjà utilisé.");
    }
  };

  return (
    <>
    {/* Skip link (WCAG 2.1 A) */}
    <a href="#auth-form" className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-[100] focus:bg-blue-600 focus:text-white focus:px-4 focus:py-2 focus:rounded-lg focus:text-sm focus:font-semibold focus:shadow-lg">Aller au formulaire</a>
    <div className="min-h-screen flex">
      {/* ── Panneau gauche — branding ── */}
      <div className="hidden lg:flex lg:w-5/12 bg-gradient-to-br from-primary-900 via-primary-800 to-primary-700 relative overflow-hidden flex-col justify-between p-12">
        {/* Fond décoratif */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-primary-600/20 rounded-full -translate-y-1/2 translate-x-1/2" />
        <div className="absolute bottom-0 left-0 w-48 h-48 bg-success-600/10 rounded-full translate-y-1/2 -translate-x-1/2" />

        {/* Logo */}
        <div className="flex items-center gap-3 relative z-10">
          <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center">
            <span className="text-white font-bold text-lg">AO</span>
          </div>
          <span className="text-white font-bold text-xl">AO Copilot</span>
        </div>

        {/* Tagline */}
        <div className="relative z-10">
          <h2 className="text-3xl font-bold text-white leading-snug mb-4">
            Gagnez vos appels<br />d&apos;offres BTP<br />
            <span className="text-primary-300">avec l&apos;IA</span>
          </h2>
          <p className="text-primary-200 text-sm leading-relaxed mb-8">
            Analysez chaque DCE en quelques minutes. Identifiez les risques,
            les exigences et les critères de notation automatiquement.
          </p>

          <ul className="space-y-3">
            {FEATURES.map(({ icon: Icon, text }) => (
              <li key={text} className="flex items-center gap-3 text-sm text-primary-100">
                <div className="w-7 h-7 rounded-lg bg-white/10 flex items-center justify-center flex-shrink-0">
                  <Icon className="w-3.5 h-3.5 text-primary-200" />
                </div>
                {text}
              </li>
            ))}
          </ul>
        </div>

        {/* Testimonial */}
        <div className="bg-white/10 rounded-2xl p-5 border border-white/10 relative z-10">
          <p className="text-primary-100 text-sm italic leading-relaxed">
            &ldquo;AO Copilot nous fait gagner 4h par DCE. L&apos;IA détecte des clauses qu&apos;on aurait ratées.&rdquo;
          </p>
          <p className="text-primary-300 text-xs mt-2 font-medium">— Responsable travaux, PME BTP 45 salariés</p>
        </div>
      </div>

      {/* ── Panneau droit — formulaire ── */}
      <div className="flex-1 flex items-center justify-center p-8 bg-surface">
        <div className="w-full max-w-md">
          {/* Header mobile */}
          <div className="flex items-center gap-2 mb-8 lg:hidden">
            <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">AO</span>
            </div>
            <span className="text-primary-700 font-bold">AO Copilot</span>
          </div>

          <div className="mb-7">
            <h1 className="text-2xl font-bold text-slate-900 mb-1">Créer votre compte</h1>
            <p className="text-slate-500 text-sm">
              Gratuit 14 jours · Pas de carte bancaire requise
            </p>
          </div>

          {/* Erreur serveur */}
          {error && (
            <div className="bg-danger-50 border border-danger-200 text-danger-700 text-sm rounded-xl px-4 py-3 mb-5">
              {error}
            </div>
          )}

          <form id="auth-form" onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {/* Nom & Entreprise */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">Prénom &amp; nom</label>
                <input
                  className="w-full px-3 py-2.5 text-sm border border-slate-200 rounded-xl focus:outline-none
                             focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
                  placeholder="Jean Dupont"
                  {...register("full_name")}
                />
                {errors.full_name && <p className="text-danger-500 text-xs mt-1">{errors.full_name.message}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">Entreprise</label>
                <input
                  className="w-full px-3 py-2.5 text-sm border border-slate-200 rounded-xl focus:outline-none
                             focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
                  placeholder="BTP Solutions SAS"
                  {...register("org_name")}
                />
                {errors.org_name && <p className="text-danger-500 text-xs mt-1">{errors.org_name.message}</p>}
              </div>
            </div>

            {/* Email */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Email professionnel</label>
              <input
                type="email"
                className="w-full px-3 py-2.5 text-sm border border-slate-200 rounded-xl focus:outline-none
                           focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
                placeholder="vous@entreprise.fr"
                {...register("email")}
              />
              {errors.email && <p className="text-danger-500 text-xs mt-1">{errors.email.message}</p>}
            </div>

            {/* Mot de passe */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Mot de passe</label>
              <input
                type="password"
                className="w-full px-3 py-2.5 text-sm border border-slate-200 rounded-xl focus:outline-none
                           focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
                placeholder="8 caractères minimum"
                {...register("password")}
              />
              {errors.password && <p className="text-danger-500 text-xs mt-1">{errors.password.message}</p>}
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="btn-primary-gradient w-full flex items-center justify-center gap-2 py-3 text-sm"
            >
              {isLoading && <Loader2 className="w-4 h-4 animate-spin" />}
              Créer mon compte gratuitement
            </button>
          </form>

          <p className="text-xs text-slate-400 text-center mt-4">
            Hébergé en France 🇫🇷 · Documents confidentiels · RGPD
          </p>

          <p className="text-center text-sm text-slate-500 mt-5">
            Déjà un compte ?{" "}
            <Link href="/login" className="text-primary-700 font-semibold hover:underline">
              Se connecter
            </Link>
          </p>
        </div>
      </div>
    </div>
    </>
  );
}
