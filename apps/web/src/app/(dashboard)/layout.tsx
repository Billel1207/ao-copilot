"use client";
import Link from "next/link";
import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard, FolderOpen, LogOut, CreditCard,
  Users, ChevronRight, Bell, Kanban, BookOpen,
  BarChart3, BookText, Building2, Code,
} from "lucide-react";
import { useAuthStore } from "@/stores/auth";
import { cn } from "@/lib/utils";
import { OnboardingModal } from "@/components/onboarding/OnboardingModal";

const navItems = [
  { href: "/dashboard",  label: "Tableau de bord", icon: LayoutDashboard },
  { href: "/projects",   label: "Projets AO",      icon: FolderOpen },
  { href: "/pipeline",   label: "Pipeline",         icon: Kanban },
  { href: "/veille",     label: "Veille AO",        icon: Bell },
  { href: "/library",    label: "Bibliothèque",     icon: BookOpen },
  { href: "/analytics",  label: "Analytics",        icon: BarChart3 },
  { href: "/glossaire",  label: "Glossaire BTP",    icon: BookText },
  { href: "/billing",    label: "Abonnement",       icon: CreditCard },
];

const bottomItems = [
  { href: "/settings/company",    label: "Mon entreprise", icon: Building2 },
  { href: "/settings/team",       label: "Équipe",          icon: Users },
  { href: "/settings/developer",  label: "Développeur",     icon: Code },
];

// ── Nav item ──────────────────────────────────────────────────────────────

function NavItem({ href, label, icon: Icon }: { href: string; label: string; icon: React.ElementType }) {
  const pathname = usePathname();
  const isActive = pathname === href || (href !== "/dashboard" && pathname.startsWith(href));

  return (
    <Link
      href={href}
      className={cn(
        "group flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150",
        isActive
          ? "bg-primary-50 text-primary-800 shadow-sm"
          : "text-slate-500 hover:bg-slate-50 hover:text-slate-800"
      )}
    >
      <Icon className={cn(
        "w-4 h-4 flex-shrink-0 transition-colors",
        isActive ? "text-primary-600" : "text-slate-400 group-hover:text-slate-600"
      )} />
      <span className="flex-1">{label}</span>
      {isActive && <ChevronRight className="w-3 h-3 text-primary-400" />}
    </Link>
  );
}

// ── Layout ────────────────────────────────────────────────────────────────

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { user, logout, fetchMe } = useAuthStore();

  // Rafraîchit le profil user au montage du layout pour s'assurer
  // que org_slug et les autres champs sont toujours à jour depuis l'API
  useEffect(() => {
    fetchMe();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Redirige vers /onboarding si l'utilisateur n'a pas encore complété l'onboarding
  useEffect(() => {
    if (user && user.onboarding_completed === false) {
      router.replace("/onboarding");
    }
  }, [user, router]);

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  const firstName = user?.full_name?.split(" ")[0] ?? user?.email?.split("@")[0] ?? "Vous";
  const initials = user?.full_name
    ? user.full_name.split(" ").map(n => n[0]).slice(0, 2).join("").toUpperCase()
    : (user?.email?.[0] ?? "?").toUpperCase();

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden">

      {/* ── Sidebar ── */}
      <aside className="w-60 bg-white border-r border-slate-100 flex flex-col flex-shrink-0 shadow-sm">

        {/* Logo */}
        <div className="px-4 py-5 border-b border-slate-100">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 bg-gradient-to-br from-primary-700 to-primary-900 rounded-lg flex items-center justify-center shadow-sm">
              <span className="text-white font-bold text-sm">AO</span>
            </div>
            <div>
              <span className="font-bold text-primary-900 text-sm block">AO Copilot</span>
              <span className="text-[10px] text-slate-400 block -mt-0.5">DCE Intelligence</span>
            </div>
          </div>
        </div>

        {/* Navigation principale */}
        <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
          {navItems.map(item => <NavItem key={item.href} {...item} />)}
        </nav>

        {/* Navigation secondaire */}
        {bottomItems.length > 0 && (
          <div className="px-3 py-2 border-t border-slate-100 space-y-0.5">
            {bottomItems.map(item => <NavItem key={item.href} {...item} />)}
          </div>
        )}

        {/* User section */}
        <div className="px-3 pb-4 pt-2 border-t border-slate-100">
          <div className="flex items-center gap-3 px-2 py-2.5 mb-1">
            {/* Avatar */}
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center flex-shrink-0 text-white text-xs font-bold shadow-sm">
              {initials}
            </div>
            <div className="min-w-0">
              <p className="text-xs font-semibold text-slate-700 truncate">{firstName}</p>
              <p className="text-[10px] text-slate-400 truncate">{user?.email}</p>
            </div>
          </div>

          <button
            onClick={handleLogout}
            className="flex items-center gap-3 w-full px-3 py-2 rounded-xl text-sm text-slate-500
                       hover:bg-danger-50 hover:text-danger-600 transition-all duration-150"
          >
            <LogOut className="w-4 h-4" />
            Déconnexion
          </button>
        </div>
      </aside>

      {/* ── Main content ── */}
      <main className="flex-1 overflow-auto min-w-0">
        {children}
      </main>

      {/* Onboarding wizard — shown once after first login */}
      <OnboardingModal />
    </div>
  );
}
