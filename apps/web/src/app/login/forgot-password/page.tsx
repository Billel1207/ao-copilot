"use client";
import { useState } from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Loader2, ArrowLeft, Mail } from "lucide-react";
import { authApi } from "@/lib/api";

const schema = z.object({
  email: z.string().email("Email invalide"),
});

type FormData = z.infer<typeof schema>;

export default function ForgotPasswordPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const onSubmit = async (data: FormData) => {
    setIsLoading(true);
    setError(null);
    try {
      await authApi.forgotPassword(data.email);
      setSent(true);
    } catch {
      setError("Une erreur est survenue. Veuillez réessayer.");
    } finally {
      setIsLoading(false);
    }
  };

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

        {sent ? (
          /* ── Confirmation envoyé ── */
          <div className="text-center space-y-4">
            <div className="w-14 h-14 bg-green-100 rounded-full flex items-center justify-center mx-auto">
              <Mail className="w-7 h-7 text-green-600" />
            </div>
            <h2 className="text-2xl font-bold text-slate-900">Email envoyé</h2>
            <p className="text-slate-500 text-sm leading-relaxed">
              Si un compte existe avec cette adresse, vous recevrez un lien de
              réinitialisation dans quelques instants. Pensez à vérifier vos
              spams.
            </p>
            <Link
              href="/login"
              className="inline-flex items-center gap-2 text-primary-800 font-semibold text-sm hover:underline mt-4"
            >
              <ArrowLeft className="w-4 h-4" />
              Retour à la connexion
            </Link>
          </div>
        ) : (
          /* ── Formulaire ── */
          <>
            <div>
              <h2 className="text-2xl font-bold text-slate-900">
                Mot de passe oublié ?
              </h2>
              <p className="text-slate-500 text-sm mt-1">
                Entrez votre adresse email pour recevoir un lien de
                réinitialisation.
              </p>
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
                    Envoi en cours...
                  </>
                ) : (
                  "Envoyer le lien →"
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
