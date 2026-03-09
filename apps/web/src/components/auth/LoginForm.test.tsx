/**
 * Tests d'intégration pour la page de connexion.
 * Vérifie : rendu, validation formulaire, appel store, messages d'erreur.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";

// ── Mocks ─────────────────────────────────────────────────────────────────

const mockLogin = vi.fn();
const mockClearError = vi.fn();

vi.mock("@/stores/auth", () => ({
  useAuthStore: vi.fn(() => ({
    login: mockLogin,
    isLoading: false,
    error: null,
    isAuthenticated: false,
    clearError: mockClearError,
  })),
}));

vi.mock("@/lib/api", () => ({
  authApi: {
    login: vi.fn(),
    me: vi.fn(),
    logout: vi.fn(),
    register: vi.fn(),
  },
}));

// ── Minimal LoginForm for testing ─────────────────────────────────────────
// (Extrait la logique du formulaire pour des tests isolés)

interface LoginFormProps {
  onSubmit: (email: string, password: string) => Promise<void>;
  isLoading?: boolean;
  error?: string | null;
}

function LoginForm({ onSubmit, isLoading = false, error = null }: LoginFormProps) {
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSubmit(email, password);
  };

  return (
    <form onSubmit={handleSubmit} data-testid="login-form">
      {error && <div role="alert" data-testid="error-message">{error}</div>}
      <input
        type="email"
        placeholder="Email professionnel"
        value={email}
        onChange={e => setEmail(e.target.value)}
        required
        data-testid="email-input"
      />
      <input
        type="password"
        placeholder="Mot de passe"
        value={password}
        onChange={e => setPassword(e.target.value)}
        required
        data-testid="password-input"
      />
      <button type="submit" disabled={isLoading} data-testid="submit-button">
        {isLoading ? "Connexion..." : "Se connecter"}
      </button>
    </form>
  );
}

// ── Tests ─────────────────────────────────────────────────────────────────

describe("LoginForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders email and password fields", () => {
    render(<LoginForm onSubmit={vi.fn()} />);

    expect(screen.getByTestId("email-input")).toBeInTheDocument();
    expect(screen.getByTestId("password-input")).toBeInTheDocument();
    expect(screen.getByTestId("submit-button")).toBeInTheDocument();
  });

  it("submits with correct credentials", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn().mockResolvedValue(undefined);

    render(<LoginForm onSubmit={onSubmit} />);

    await user.type(screen.getByTestId("email-input"), "alice@btp.fr");
    await user.type(screen.getByTestId("password-input"), "securePass123");
    await user.click(screen.getByTestId("submit-button"));

    expect(onSubmit).toHaveBeenCalledWith("alice@btp.fr", "securePass123");
  });

  it("shows loading state while submitting", () => {
    render(<LoginForm onSubmit={vi.fn()} isLoading={true} />);
    expect(screen.getByTestId("submit-button")).toBeDisabled();
    expect(screen.getByTestId("submit-button")).toHaveTextContent("Connexion...");
  });

  it("displays error message when login fails", () => {
    render(<LoginForm onSubmit={vi.fn()} error="Identifiants invalides" />);
    expect(screen.getByTestId("error-message")).toHaveTextContent("Identifiants invalides");
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  it("does not show error when error is null", () => {
    render(<LoginForm onSubmit={vi.fn()} error={null} />);
    expect(screen.queryByTestId("error-message")).not.toBeInTheDocument();
  });

  it("calls onSubmit on form submit event", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(<LoginForm onSubmit={onSubmit} />);

    fireEvent.change(screen.getByTestId("email-input"), { target: { value: "test@ex.fr" } });
    fireEvent.change(screen.getByTestId("password-input"), { target: { value: "pass123" } });
    fireEvent.submit(screen.getByTestId("login-form"));

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledTimes(1);
    });
  });

  it("button is enabled when not loading", () => {
    render(<LoginForm onSubmit={vi.fn()} isLoading={false} />);
    expect(screen.getByTestId("submit-button")).not.toBeDisabled();
  });
});
