/**
 * Tests unitaires pour le store d'authentification Zustand.
 * Couvre : login success, login failure, register, logout, fetchMe.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";

// ── Mocks ────────────────────────────────────────────────────────────────

vi.mock("@/lib/api", () => ({
  authApi: {
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    me: vi.fn(),
  },
}));

vi.mock("js-cookie", () => ({
  default: {
    set: vi.fn(),
    remove: vi.fn(),
    get: vi.fn(),
  },
}));

// ── Imports (après les mocks) ────────────────────────────────────────────

import { useAuthStore } from "./auth";
import { authApi } from "@/lib/api";
import Cookies from "js-cookie";

const mockAuthApi = authApi as {
  login: ReturnType<typeof vi.fn>;
  register: ReturnType<typeof vi.fn>;
  logout: ReturnType<typeof vi.fn>;
  me: ReturnType<typeof vi.fn>;
};

const MOCK_USER = {
  id: "user-123",
  email: "alice@btp.fr",
  full_name: "Alice Martin",
  role: "admin",
  org_id: "org-456",
};

const MOCK_TOKENS = {
  access_token: "tok_abc123",
  token_type: "bearer",
};

// ── Helpers ──────────────────────────────────────────────────────────────

function resetStore() {
  useAuthStore.setState({
    user: null,
    isLoading: false,
    isAuthenticated: false,
    error: null,
  });
}

// ── Tests ────────────────────────────────────────────────────────────────

describe("useAuthStore — login()", () => {
  beforeEach(() => {
    resetStore();
    vi.clearAllMocks();
  });

  it("sets user and isAuthenticated on success", async () => {
    mockAuthApi.login.mockResolvedValue({ data: MOCK_TOKENS });
    mockAuthApi.me.mockResolvedValue({ data: MOCK_USER });

    await useAuthStore.getState().login("alice@btp.fr", "password123");

    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(true);
    expect(state.user).toMatchObject({ email: "alice@btp.fr", role: "admin" });
    expect(state.error).toBeNull();
    expect(state.isLoading).toBe(false);
    expect(Cookies.set).toHaveBeenCalledWith("access_token", "tok_abc123", expect.any(Object));
  });

  it("sets error and throws on failure", async () => {
    const apiError = { response: { data: { detail: "Identifiants invalides" } } };
    mockAuthApi.login.mockRejectedValue(apiError);

    await expect(useAuthStore.getState().login("bad@email.fr", "wrong")).rejects.toBeDefined();

    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(false);
    expect(state.user).toBeNull();
    expect(state.error).toBe("Identifiants invalides");
    expect(state.isLoading).toBe(false);
  });

  it("uses fallback error message when detail is missing", async () => {
    mockAuthApi.login.mockRejectedValue(new Error("Network Error"));

    await expect(useAuthStore.getState().login("x@y.fr", "pass")).rejects.toBeDefined();
    expect(useAuthStore.getState().error).toBe("Erreur de connexion. Vérifiez vos identifiants.");
  });

  it("always resets isLoading to false after login attempt", async () => {
    mockAuthApi.login.mockRejectedValue(new Error("fail"));

    await useAuthStore.getState().login("x@y.fr", "pass").catch(() => {});
    expect(useAuthStore.getState().isLoading).toBe(false);
  });
});

describe("useAuthStore — register()", () => {
  beforeEach(() => {
    resetStore();
    vi.clearAllMocks();
  });

  it("creates account and sets user on success", async () => {
    mockAuthApi.register.mockResolvedValue({ data: MOCK_TOKENS });
    mockAuthApi.me.mockResolvedValue({ data: MOCK_USER });

    await useAuthStore.getState().register({
      email: "alice@btp.fr",
      password: "securePass123",
      full_name: "Alice Martin",
      org_name: "BTP Solutions",
    });

    expect(useAuthStore.getState().isAuthenticated).toBe(true);
    expect(useAuthStore.getState().user?.email).toBe("alice@btp.fr");
  });

  it("sets error on registration failure", async () => {
    const apiError = { response: { data: { detail: "Email déjà utilisé" } } };
    mockAuthApi.register.mockRejectedValue(apiError);

    await useAuthStore.getState().register({
      email: "exists@btp.fr",
      password: "pass",
      full_name: "Test",
      org_name: "Org",
    }).catch(() => {});

    expect(useAuthStore.getState().error).toBe("Email déjà utilisé");
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
  });
});

describe("useAuthStore — logout()", () => {
  beforeEach(() => {
    useAuthStore.setState({ user: MOCK_USER, isAuthenticated: true, error: null });
    vi.clearAllMocks();
  });

  it("clears user state and removes cookie", async () => {
    mockAuthApi.logout.mockResolvedValue({});

    await useAuthStore.getState().logout();

    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.isAuthenticated).toBe(false);
    expect(Cookies.remove).toHaveBeenCalledWith("access_token");
  });

  it("clears state even when API call fails", async () => {
    mockAuthApi.logout.mockRejectedValue(new Error("Network error"));

    await useAuthStore.getState().logout();

    expect(useAuthStore.getState().user).toBeNull();
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
  });
});

describe("useAuthStore — fetchMe()", () => {
  beforeEach(() => resetStore());

  it("sets user when API returns valid user", async () => {
    mockAuthApi.me.mockResolvedValue({ data: MOCK_USER });

    await useAuthStore.getState().fetchMe();

    expect(useAuthStore.getState().user).toMatchObject(MOCK_USER);
    expect(useAuthStore.getState().isAuthenticated).toBe(true);
  });

  it("clears state when API returns error (token expired)", async () => {
    mockAuthApi.me.mockRejectedValue(new Error("401"));

    await useAuthStore.getState().fetchMe();

    expect(useAuthStore.getState().user).toBeNull();
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
  });
});

describe("useAuthStore — clearError()", () => {
  it("clears existing error", () => {
    useAuthStore.setState({ error: "Some error" });
    useAuthStore.getState().clearError();
    expect(useAuthStore.getState().error).toBeNull();
  });
});
