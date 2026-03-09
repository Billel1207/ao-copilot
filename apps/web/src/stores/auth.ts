import { create } from "zustand";
import { persist } from "zustand/middleware";
import Cookies from "js-cookie";
import { authApi } from "@/lib/api";

interface User {
  id: string;
  email: string;
  full_name: string | null;
  role: string;
  org_id: string;
  org_slug?: string;
  onboarding_completed: boolean;
}

interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (data: { email: string; password: string; full_name: string; org_name: string }) => Promise<void>;
  logout: () => Promise<void>;
  fetchMe: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isLoading: false,
      isAuthenticated: false,
      error: null,

      clearError: () => set({ error: null }),

      login: async (email, password) => {
        set({ isLoading: true, error: null });
        try {
          const { data } = await authApi.login({ email, password });
          Cookies.set("access_token", data.access_token, {
            expires: 1 / 96, // 15 min
            sameSite: "lax",
            secure: process.env.NODE_ENV === "production",
          });
          const meRes = await authApi.me();
          set({ user: meRes.data, isAuthenticated: true });
        } catch (err: unknown) {
          const message =
            (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
            "Erreur de connexion. Vérifiez vos identifiants.";
          set({ error: message, isAuthenticated: false });
          throw err; // re-throw pour que la page puisse réagir
        } finally {
          set({ isLoading: false });
        }
      },

      register: async (data) => {
        set({ isLoading: true, error: null });
        try {
          const { data: res } = await authApi.register(data);
          Cookies.set("access_token", res.access_token, {
            expires: 1 / 96,
            sameSite: "lax",
            secure: process.env.NODE_ENV === "production",
          });
          const meRes = await authApi.me();
          set({ user: meRes.data, isAuthenticated: true });
        } catch (err: unknown) {
          const message =
            (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
            "Erreur lors de la création du compte.";
          set({ error: message, isAuthenticated: false });
          throw err;
        } finally {
          set({ isLoading: false });
        }
      },

      logout: async () => {
        await authApi.logout().catch(() => {});
        Cookies.remove("access_token");
        set({ user: null, isAuthenticated: false, error: null });
      },

      fetchMe: async () => {
        try {
          const { data } = await authApi.me();
          set({ user: data, isAuthenticated: true });
        } catch {
          set({ user: null, isAuthenticated: false });
        }
      },
    }),
    {
      name: "auth-store",
      partialize: (state) => ({ user: state.user, isAuthenticated: state.isAuthenticated }),
    }
  )
);
