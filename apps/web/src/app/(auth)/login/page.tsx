"use client";
import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { Loader2, ShieldCheck, TrendingUp, FileCheck2 } from "lucide-react";
import { useAuthStore } from "@/stores/auth";

const schema = z.object({
  email: z.string().email("Email invalide"),
  password: z.string().min(1, "Mot de passe requis"),
});

type FormData = z.infer<typeof schema>;

const FEATURES = [
  {
    icon: <FileCheck2 className="w-5 h-5" />,
    title: "Analyse automatique des DCE",
    desc: "Résumé, checklist de conformité et critères d'évaluation en quelques minutes.",
  },
  {
    icon: <ShieldCheck className="w-5 h-5" />,
    title: "Zéro risque oublié",
    desc: "IA calibrée sur des centaines de DCE BTP — détecte les pièges contractuels.",
  },
  {
    icon: <TrendingUp className="w-5 h-5" />,
    title: "Réponse 3× plus rapide",
    desc: "Concentrez-vous sur la rédaction, pas sur la lecture des 200 pages de RC.",
  },
];

export default function LoginPage() {
  const router = useRouter();
  const { login, isLoading } = useAuthStore();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const onSubmit = async (data: FormData) => {
    try {
      await login(data.email, data.password);
      router.push("/dashboard");
    } catch {
      toast.error("Email ou mot de passe incorrect");
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* ── Panneau gauche — gradient + branding ── */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-primary-900 via-primary-800 to-primary-700
                      flex-col justify-between p-10 relative overflow-hidden">
        {/* Motif décoratif */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-20 left-10 w-64 h-64 bg-white rounded-full blur-3xl" />
          <div className="absolute bottom-20 right-10 w-96 h-96 bg-blue-300 rounded-full blur-3xl" />
        </div>

        {/* Logo */}
        <div className="relative z-10 flex items-center gap-3">
          <div className="w-9 h-9 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
            <span className="text-white font-bold text-sm">AO</span>
          </div>
          <span className="text-white font-semibold text-lg">AO Copilot</span>
        </div>

        {/* Tagline centrale */}
        <div className="relative z-10 space-y-6">
          <div className="space-y-3">
            <h1 className="text-4xl font-extrabold text-white leading-tight">
              Analysez vos DCE<br />
              <span className="text-blue-200">10× plus vite</span>
            </h1>
            <p className="text-blue-100 text-lg leading-relaxed max-w-sm">
              L&apos;IA qui lit vos appels d&apos;offres BTP à votre place — et ne rate aucun détail critique.
            </p>
          </div>

          {/* Features */}
          <div className="space-y-4">
            {FEATURES.map((f, i) => (
              <div key={i} className="flex items-start gap-3 animate-slide-up"
                style={{ animationDelay: `${i * 80}ms` }}>
                <div className="w-8 h-8 bg-white/15 rounded-lg flex items-center justify-center
                                text-blue-200 flex-shrink-0 mt-0.5">
                  {f.icon}
                </div>
                <div>
                  <p className="text-white font-semibold text-sm">{f.title}</p>
                  <p className="text-blue-200 text-xs mt-0.5 leading-relaxed">{f.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer témoignage */}
        <div className="relative z-10 bg-white/10 rounded-2xl p-4 backdrop-blur-sm border border-white/20">
          <p className="text-blue-100 text-sm italic leading-relaxed">
            &ldquo;Nous avons réduit notre temps de réponse aux AO de 4 jours à moins de 6 heures.&rdquo;
          </p>
          <p className="text-blue-300 text-xs mt-2 font-medium">
            — Directeur Technique, ETI BTP (Île-de-France)
          </p>
        </div>
      </div>

      {/* ── Panneau droit — formulaire ── */}
      <div className="flex-1 flex items-center justify-center p-8 bg-surface-50">
        <div className="w-full max-w-sm space-y-8 animate-fade-in">
          {/* Mobile logo */}
          <div className="lg:hidden flex items-center gap-2 justify-center">
            <div className="w-8 h-8 bg-primary-800 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-xs">AO</span>
            </div>
            <span className="font-bold text-primary-900">AO Copilot</span>
          </div>

          <div>
            <h2 className="text-2xl font-bold text-slate-900">Connexion</h2>
            <p className="text-slate-500 text-sm mt-1">Content de vous revoir !</p>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">
                Adresse email
              </label>
              <input
                type="email"
                className="input-field"
                placeholder="vous@entreprise.fr"
                autoComplete="email"
                {...register("email")}
              />
              {errors.email && (
                <p className="text-danger-600 text-xs mt-1.5 flex items-center gap-1">
                  <span>⚠</span> {errors.email.message}
                </p>
              )}
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="block text-sm font-medium text-slate-700">Mot de passe</label>
              </div>
              <input
                type="password"
                className="input-field"
                placeholder="••••••••"
                autoComplete="current-password"
                {...register("password")}
              />
              {errors.password && (
                <p className="text-danger-600 text-xs mt-1.5 flex items-center gap-1">
                  <span>⚠</span> {errors.password.message}
                </p>
              )}
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="btn-primary-gradient w-full flex items-center justify-center gap-2 py-3"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Connexion...
                </>
              ) : (
                "Se connecter →"
              )}
            </button>
          </form>

          <p className="text-center text-sm text-slate-500">
            Pas encore de compte ?{" "}
            <Link href="/register" className="text-primary-800 font-semibold hover:underline">
              Créer un compte gratuit
            </Link>
          </p>

          {/* Badges confiance */}
          <div className="flex items-center justify-center gap-4 pt-2">
            {["🔒 RGPD", "🇫🇷 Hébergé en France", "⚡ 14 jours essai"].map((t) => (
              <span key={t} className="text-xs text-slate-400">{t}</span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
