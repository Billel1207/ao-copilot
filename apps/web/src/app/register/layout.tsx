import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Créer un compte — AO Copilot",
  description:
    "Créez votre compte AO Copilot gratuitement et commencez à analyser vos DCE BTP en 5 minutes.",
  robots: { index: true, follow: true },
};

export default function RegisterLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
