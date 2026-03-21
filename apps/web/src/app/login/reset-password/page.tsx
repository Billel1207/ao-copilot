"use client";
import { Suspense, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Loader2, ArrowLeft, CheckCircle2 } from "lucide-react";
import { authApi } from "@/lib/api";

const schema = z
  .object({
    password: z
      .string()
      .min(8, "Minimum 8 caractères")
      .regex(/[A-Z]/, "Au moins une majuscule")
      .regex(/[a-z]/, "Au moins une minuscule")
      .regex(/\d/, "Au moins un chiffre"),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Les mots de passe ne correspondent pas",
    path: ["confirmPassword"],
  });

type FormData = z.infer<typeof schema>;

function ResetPasswordContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  const [isLoading, setIsLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const onSubmit = async (data: FormData) => {
    if (!token) return;
    setIsLoading(true);
    setError(null);
    try {
      await authApi.resetPassword(token, data.password);
      setSuccess(true);
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      setError(
        axiosErr?.response?.data?.detail ||
          "Le lien est invalide ou a expiré. Veuillez refaire une demande."
      );
    } finally {
      setIsLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center p-8 bg-surface-50">
        <div className="w-full max-w-sm text-center space-y-4 animate-fade-in">
          <h2 className="text-2xl font-bold text-slate-900">Lien invalide</h2>
          <p className="text-slate-500 text-sm">
            Le lien de réinitialisation est manquant ou invalide.
          </p>
          <Link
            href="/login/forgot-password"
            className="inline-flex items-center gap-2 text-primary-800 font-semibold text-sm hover:underline"
          >
            Demander un nouveau lien →
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-8 bg-surface-50">
      <div className="w-full max-w-sm space-y-8 animate-fade-in">
        {/* Logo */}
        <div className="flex items-center gap-2 justify-center">
          <div className="w-8 h-8 bg-primary-800 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-xs">AO</span>
          </div>
          <span className="font-bold text-primary-900">AO Copilot</span>
        </div>

        {success ? (
          /* ── Succès ── */
          <div className="text-center space-y-4">
            <div className="w-14 h-14 bg-green-100 rounded-full flex items-center justify-center mx-auto">
              <CheckCircle2 className="w-7 h-7 text-green-600" />
            </div>
            <h2 className="text-2xl font-bold text-slate-900">
              Mot de passe modifié
            </h2>
            <p className="text-slate-500 text-sm leading-relaxed">
              Votre mot de passe a été réinitialisé avec succès. Vous pouvez
              maintenant vous connecter.
            </p>
            <Link
              href="/login"
              className="btn-primary-gradient inline-flex items-center gap-2 px-6 py-3"
            >
              Se connecter →
            </Link>
          </div>
        ) : (
          /* ── Formulaire ── */
          <>
            <div>
              <h2 className="text-2xl font-bold text-slate-900">
                Nouveau mot de passe
              </h2>
              <p className="text-slate-500 text-sm mt-1">
                Choisissez un nouveau mot de passe sécurisé.
              </p>
            </div>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">
                  Nouveau mot de passe
                </label>
                <input
                  type="password"
                  className="input-field"
                  placeholder="••••••••"
                  autoComplete="new-password"
                  {...register("password")}
                />
                {errors.password && (
                  <p className="text-danger-600 text-xs mt-1.5 flex items-center gap-1">
                    <span>⚠</span> {errors.password.message}
                  </p>
                )}
                <p className="text-slate-400 text-xs mt-1">
                  Min. 8 caractères, 1 majuscule, 1 minuscule, 1 chiffre
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">
                  Confirmer le mot de passe
                </label>
                <input
                  type="password"
                  className="input-field"
                  placeholder="••••••••"
                  autoComplete="new-password"
                  {...register("confirmPassword")}
                />
                {errors.confirmPassword && (
                  <p className="text-danger-600 text-xs mt-1.5 flex items-center gap-1">
                    <span>⚠</span> {errors.confirmPassword.message}
                  </p>
                )}
              </div>

              {error && (
                <p className="text-danger-600 text-sm text-center">{error}</p>
              )}

              <button
                type="submit"
                disabled={isLoading}
                className="btn-primary-gradient w-full flex items-center justify-center gap-2 py-3"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Réinitialisation...
                  </>
                ) : (
                  "Réinitialiser le mot de passe →"
                )}
              </button>
            </form>

            <p className="text-center text-sm text-slate-500">
              <Link
                href="/login"
                className="inline-flex items-center gap-1 text-primary-800 font-semibold hover:underline"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                Retour à la connexion
              </Link>
            </p>
          </>
        )}
      </div>
    </div>
  );
}


export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center"><Loader2 className="w-6 h-6 animate-spin text-primary-600" /></div>}>
      <ResetPasswordContent />
    </Suspense>
  );
}
