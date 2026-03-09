// Layout passthrough — login et register définissent leur propre mise en page full-screen
export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
