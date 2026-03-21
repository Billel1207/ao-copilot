import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Se connecter — AO Copilot",
  description:
    "Connectez-vous à AO Copilot pour analyser vos appels d'offres BTP avec l'intelligence artificielle.",
  robots: { index: false, follow: false },
};

export default function LoginLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
