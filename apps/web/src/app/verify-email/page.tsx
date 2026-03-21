"use client";
import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Loader2, CheckCircle2, XCircle } from "lucide-react";
import { authApi } from "@/lib/api";

function VerifyEmailContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  const [status, setStatus] = useState<"loading" | "success" | "already" | "error">("loading");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      setStatus("error");
      setError("Lien de vérification manquant ou invalide.");
      return;
    }

    let cancelled = false;

    async function verify() {
      try {
        const { data } = await authApi.verifyEmail(token!);
        if (cancelled) return;
        if (data?.message?.includes("déjà")) {
          setStatus("already");
        } else {
          setStatus("success");
        }
      } catch (err: unknown) {
        if (cancelled) return;
        const axiosErr = err as { response?: { data?: { detail?: string } } };
        setError(
          axiosErr?.response?.data?.detail ||
            "Le lien est invalide ou a expiré."
        );
        setStatus("error");
      }
    }

    verify();

    return () => {
      cancelled = true;
    };
  }, [token]);

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

        {status === "loading" && (
          <div className="text-center space-y-4">
            <div className="w-14 h-14 bg-blue-100 rounded-full flex items-center justify-center mx-auto">
              <Loader2 className="w-7 h-7 text-blue-600 animate-spin" />
            </div>
            <h2 className="text-2xl font-bold text-slate-900">
              Vérification en cours...
            </h2>
            <p className="text-slate-500 text-sm leading-relaxed">
              Veuillez patienter pendant que nous vérifions votre adresse email.
            </p>
          </div>
        )}

        {(status === "success" || status === "already") && (
          <div className="text-center space-y-4">
            <div className="w-14 h-14 bg-green-100 rounded-full flex items-center justify-center mx-auto">
              <CheckCircle2 className="w-7 h-7 text-green-600" />
            </div>
            <h2 className="text-2xl font-bold text-slate-900">
              {status === "already" ? "Email déjà vérifié" : "Email vérifié !"}
            </h2>
            <p className="text-slate-500 text-sm leading-relaxed">
              {status === "already"
                ? "Votre adresse email a déjà été confirmée. Vous pouvez continuer à utiliser AO Copilot."
                : "Votre adresse email a été confirmée avec succès. Vous pouvez maintenant accéder à toutes les fonctionnalités."}
            </p>
            <Link
              href="/login"
              className="btn-primary-gradient inline-flex items-center gap-2 px-6 py-3"
            >
              Continuer vers AO Copilot
            </Link>
          </div>
        )}

        {status === "error" && (
          <div className="text-center space-y-4">
            <div className="w-14 h-14 bg-red-100 rounded-full flex items-center justify-center mx-auto">
              <XCircle className="w-7 h-7 text-red-600" />
            </div>
            <h2 className="text-2xl font-bold text-slate-900">
              Erreur de vérification
            </h2>
            <p className="text-slate-500 text-sm leading-relaxed">
              {error}
            </p>
            <div className="space-y-2">
              <Link
                href="/login"
                className="btn-primary-gradient inline-flex items-center gap-2 px-6 py-3"
              >
                Retour à la connexion
              </Link>
              <p className="text-slate-400 text-xs">
                Le lien de vérification expire après 24 heures. Connectez-vous pour en recevoir un nouveau.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}


export default function VerifyEmailPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center"><Loader2 className="w-6 h-6 animate-spin text-primary-600" /></div>}>
      <VerifyEmailContent />
    </Suspense>
  );
}
