"use client";

export const dynamic = "force-dynamic";
import { useState } from "react";
import {
  Users, UserPlus, Mail, Shield, ShieldCheck,
  Clock, Trash2, Loader2, CheckCircle2, AlertCircle, Crown
} from "lucide-react";
import { toast } from "sonner";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api";
import { useAuthStore } from "@/stores/auth";

// ── Types ────────────────────────────────────────────────────────────────

interface Member {
  id: string;
  email: string;
  full_name: string | null;
  role: "member" | "admin" | "owner";
  created_at: string;
  last_login_at: string | null;
}

interface Invite {
  id: string;
  email: string;
  role: "member" | "admin";
  invited_by_name: string | null;
  created_at: string;
  expires_at: string;
  accepted: boolean;
}

// ── Role badge ────────────────────────────────────────────────────────────

function RoleBadge({ role }: { role: string }) {
  const configs: Record<string, { label: string; icon: React.ReactNode; class: string }> = {
    owner: {
      label: "Propriétaire",
      icon: <Crown className="w-3 h-3" />,
      class: "bg-amber-100 text-amber-800",
    },
    admin: {
      label: "Admin",
      icon: <Shield className="w-3 h-3" />,
      class: "bg-primary-100 text-primary-800",
    },
    member: {
      label: "Membre",
      icon: <ShieldCheck className="w-3 h-3" />,
      class: "bg-slate-100 text-slate-600",
    },
  };
  const cfg = configs[role] ?? configs.member;
  return (
    <span className={`inline-flex items-center gap-1 text-[10px] font-bold px-1.5 py-0.5 rounded ${cfg.class}`}>
      {cfg.icon}
      {cfg.label}
    </span>
  );
}

// ── Invite Form ───────────────────────────────────────────────────────────

function InviteForm({ orgSlug }: { orgSlug: string }) {
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<"member" | "admin">("member");
  const queryClient = useQueryClient();

  const inviteMutation = useMutation({
    mutationFn: async (data: { email: string; role: string }) => {
      const res = await apiClient.post(`/api/v1/team/${orgSlug}/invite`, data);
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Erreur lors de l'invitation");
      }
      return res.json();
    },
    onSuccess: () => {
      toast.success(`Invitation envoyée à ${email}`);
      setEmail("");
      queryClient.invalidateQueries({ queryKey: ["team-invites", orgSlug] });
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) return;
    inviteMutation.mutate({ email: email.trim(), role });
  };

  return (
    <form onSubmit={handleSubmit} className="card p-5">
      <h3 className="text-sm font-semibold text-slate-700 mb-4 flex items-center gap-2">
        <UserPlus className="w-4 h-4 text-primary-600" />
        Inviter un collaborateur
      </h3>

      <div className="flex flex-col sm:flex-row gap-3">
        <input
          type="email"
          value={email}
          onChange={e => setEmail(e.target.value)}
          placeholder="prenom@entreprise.fr"
          required
          className="flex-1 px-3 py-2 text-sm border border-slate-200 rounded-xl focus:outline-none
                     focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
        />
        <select
          value={role}
          onChange={e => setRole(e.target.value as "member" | "admin")}
          className="px-3 py-2 text-sm border border-slate-200 rounded-xl focus:outline-none
                     focus:ring-2 focus:ring-primary-500 bg-white transition-all"
        >
          <option value="member">Membre</option>
          <option value="admin">Admin</option>
        </select>
        <button
          type="submit"
          disabled={inviteMutation.isPending || !email.trim()}
          className="btn-primary-gradient flex items-center gap-2 px-5 whitespace-nowrap"
        >
          {inviteMutation.isPending ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Mail className="w-4 h-4" />
          )}
          Envoyer l&apos;invitation
        </button>
      </div>

      <p className="text-xs text-slate-400 mt-3">
        L&apos;invitation est valable 7 jours. Un email sera envoyé automatiquement.
      </p>
    </form>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────

export default function TeamPage() {
  const { user } = useAuthStore();
  const orgSlug = user?.org_slug ?? "";
  const queryClient = useQueryClient();
  const isAdmin = user?.role === "admin" || user?.role === "owner";

  // Fetch members
  const { data: members = [], isLoading: loadingMembers } = useQuery<Member[]>({
    queryKey: ["team-members", orgSlug],
    queryFn: async () => {
      const res = await apiClient.get(`/api/v1/team/${orgSlug}/members`);
      if (!res.ok) throw new Error("Erreur chargement membres");
      return res.json();
    },
    enabled: !!orgSlug,
  });

  // Fetch pending invites
  const { data: invites = [], isLoading: loadingInvites } = useQuery<Invite[]>({
    queryKey: ["team-invites", orgSlug],
    queryFn: async () => {
      const res = await apiClient.get(`/api/v1/team/${orgSlug}/invites`);
      if (!res.ok) throw new Error("Erreur chargement invitations");
      return res.json();
    },
    enabled: !!orgSlug && isAdmin,
  });

  // Cancel invite mutation
  const cancelInvite = useMutation({
    mutationFn: async (inviteId: string) => {
      const res = await apiClient.delete(`/api/v1/team/${orgSlug}/invites/${inviteId}`);
      if (!res.ok) throw new Error("Erreur annulation");
    },
    onSuccess: () => {
      toast.success("Invitation annulée");
      queryClient.invalidateQueries({ queryKey: ["team-invites", orgSlug] });
    },
    onError: () => toast.error("Impossible d'annuler l'invitation"),
  });

  // Change role mutation
  const changeRole = useMutation({
    mutationFn: async ({ memberId, role }: { memberId: string; role: string }) => {
      const res = await apiClient.patch(`/api/v1/team/${orgSlug}/members/${memberId}/role`, { role });
      if (!res.ok) throw new Error("Erreur changement rôle");
    },
    onSuccess: () => {
      toast.success("Rôle mis à jour");
      queryClient.invalidateQueries({ queryKey: ["team-members", orgSlug] });
    },
    onError: () => toast.error("Impossible de modifier le rôle"),
  });

  const formatDate = (iso: string) =>
    new Date(iso).toLocaleDateString("fr-FR", { day: "numeric", month: "short", year: "numeric" });

  const daysLeft = (expires: string) => {
    const diff = new Date(expires).getTime() - Date.now();
    return Math.ceil(diff / (1000 * 60 * 60 * 24));
  };

  return (
    <div className="p-6 md:p-8 max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
          <Users className="w-5 h-5 text-primary-600" />
          Gestion de l&apos;équipe
        </h1>
        <p className="text-slate-500 text-sm mt-1">
          {members.length} membre{members.length > 1 ? "s" : ""} dans votre organisation
        </p>
      </div>

      {/* Invite form — admin only */}
      {isAdmin && <div className="mb-8"><InviteForm orgSlug={orgSlug} /></div>}

      {/* Members list */}
      <section className="mb-8">
        <h2 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
          <Users className="w-4 h-4 text-slate-400" />
          Membres ({members.length})
        </h2>

        <div className="card overflow-hidden">
          {loadingMembers ? (
            <div className="p-8 text-center text-slate-400 text-sm">
              <Loader2 className="w-5 h-5 animate-spin mx-auto mb-2" />
              Chargement...
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-100">
                  <th className="text-left px-4 py-3 font-semibold text-slate-500">Utilisateur</th>
                  <th className="text-left px-4 py-3 font-semibold text-slate-500">Rôle</th>
                  <th className="text-left px-4 py-3 font-semibold text-slate-500 hidden md:table-cell">Dernière connexion</th>
                  {isAdmin && <th className="px-4 py-3 w-24" />}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {members.map(m => (
                  <tr key={m.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="px-4 py-3">
                      <p className="font-medium text-slate-800">{m.full_name || m.email}</p>
                      <p className="text-xs text-slate-400">{m.full_name ? m.email : ""}</p>
                    </td>
                    <td className="px-4 py-3">
                      <RoleBadge role={m.role} />
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-400 hidden md:table-cell">
                      {m.last_login_at ? formatDate(m.last_login_at) : "Jamais"}
                    </td>
                    {isAdmin && (
                      <td className="px-4 py-3">
                        {m.id !== user?.id && m.role !== "owner" && (
                          <select
                            defaultValue={m.role}
                            onChange={e => changeRole.mutate({ memberId: m.id, role: e.target.value })}
                            className="text-xs border border-slate-200 rounded-lg px-2 py-1 bg-white
                                       focus:outline-none focus:ring-1 focus:ring-primary-500"
                          >
                            <option value="member">Membre</option>
                            <option value="admin">Admin</option>
                          </select>
                        )}
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </section>

      {/* Pending invites — admin only */}
      {isAdmin && (
        <section>
          <h2 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
            <Clock className="w-4 h-4 text-amber-500" />
            Invitations en attente ({invites.length})
          </h2>

          {loadingInvites ? (
            <div className="card p-6 text-center text-slate-400 text-sm">
              <Loader2 className="w-4 h-4 animate-spin mx-auto" />
            </div>
          ) : invites.length === 0 ? (
            <div className="card p-6 text-center text-slate-400 text-sm">
              <CheckCircle2 className="w-5 h-5 mx-auto mb-2 text-success-500" />
              Aucune invitation en attente
            </div>
          ) : (
            <div className="space-y-2">
              {invites.map(inv => {
                const days = daysLeft(inv.expires_at);
                return (
                  <div key={inv.id} className="card p-4 flex items-center justify-between gap-4">
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="w-8 h-8 rounded-full bg-primary-50 flex items-center justify-center flex-shrink-0">
                        <Mail className="w-4 h-4 text-primary-500" />
                      </div>
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-slate-800 truncate">{inv.email}</p>
                        <p className="text-xs text-slate-400">
                          Invité par {inv.invited_by_name ?? "—"} · expire dans {days}j
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 flex-shrink-0">
                      <RoleBadge role={inv.role} />
                      {days <= 2 && (
                        <span className="flex items-center gap-1 text-xs text-danger-600">
                          <AlertCircle className="w-3 h-3" />
                          Expire bientôt
                        </span>
                      )}
                      <button
                        onClick={() => cancelInvite.mutate(inv.id)}
                        disabled={cancelInvite.isPending}
                        className="text-slate-300 hover:text-danger-400 transition-colors p-1.5
                                   rounded-lg hover:bg-danger-50"
                        title="Annuler l'invitation"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </section>
      )}
    </div>
  );
}
