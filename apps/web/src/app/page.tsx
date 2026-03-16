"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import Link from "next/link";

// --------------------------------------------------------------------------
// Utility — IntersectionObserver hook
// --------------------------------------------------------------------------
function useReveal() {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { threshold: 0.12 }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return { ref, visible };
}

// --------------------------------------------------------------------------
// SVG Icons
// --------------------------------------------------------------------------
const IconBrain = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15m-6.75-11.896c.251.023.501.05.75.082M3 16.5v-1.5a3 3 0 013-3h12a3 3 0 013 3v1.5M3 16.5A2.25 2.25 0 005.25 18.75h13.5A2.25 2.25 0 0021 16.5M3 16.5h18" />
  </svg>
);

const IconShield = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
  </svg>
);

const IconGoNoGo = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
  </svg>
);

const IconDoc = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
  </svg>
);

const IconExcel = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M3.375 19.5h17.25m-17.25 0a1.125 1.125 0 01-1.125-1.125M3.375 19.5h1.5C5.496 19.5 6 18.996 6 18.375m-3.75 0V5.625m0 12.75v-1.5c0-.621.504-1.125 1.125-1.125m18.375 2.625V5.625m0 12.75c0 .621-.504 1.125-1.125 1.125m1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125m0 3.75h-1.5A1.125 1.125 0 0118 18.375M20.625 4.5H3.375m17.25 0c.621 0 1.125.504 1.125 1.125M20.625 4.5h-1.5C18.504 4.5 18 5.004 18 5.625m3.75 0v1.5c0 .621-.504 1.125-1.125 1.125M3.375 4.5c-.621 0-1.125.504-1.125 1.125M3.375 4.5h1.5C5.496 4.5 6 5.004 6 5.625m-3.75 0v1.5c0 .621.504 1.125 1.125 1.125m0 0h1.5m-1.5 0c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125m1.5-3.75C5.496 8.25 6 7.746 6 7.125v-1.5M4.875 8.25C5.496 8.25 6 8.754 6 9.375v1.5m0-5.25v5.25m0-5.25C6 5.004 6.504 4.5 7.125 4.5h9.75c.621 0 1.125.504 1.125 1.125m1.125 2.625h1.5m-1.5 0A1.125 1.125 0 0118 7.125v-1.5m1.125 2.625c-.621 0-1.125.504-1.125 1.125v1.5m2.625-2.625c.621 0 1.125.504 1.125 1.125v1.5c0 .621-.504 1.125-1.125 1.125M18 5.625v5.25M7.125 12h9.75m-9.75 0A1.125 1.125 0 016 10.875M7.125 12C6.504 12 6 12.504 6 13.125m0-2.25C6 11.496 5.496 12 4.875 12M18 10.875c0 .621-.504 1.125-1.125 1.125M18 10.875c.621 0 1.125.504 1.125 1.125v1.5c0 .621-.504 1.125-1.125 1.125m-7.5 0h6.375" />
  </svg>
);

const IconBell = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
  </svg>
);

const IconCheck = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
  </svg>
);

const IconChevron = ({ open }: { open: boolean }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    className={`w-5 h-5 text-slate-500 transition-transform duration-200 ${open ? "rotate-180" : ""}`}
    fill="none"
    viewBox="0 0 24 24"
    stroke="currentColor"
    strokeWidth={2}
  >
    <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
  </svg>
);

// --------------------------------------------------------------------------
// Navbar
// --------------------------------------------------------------------------
function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 10);
    window.addEventListener("scroll", handler, { passive: true });
    return () => window.removeEventListener("scroll", handler);
  }, []);

  const scrollTo = (id: string) => {
    setMenuOpen(false);
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 bg-white/95 backdrop-blur-sm transition-shadow duration-200 ${
        scrolled ? "shadow-md" : "shadow-none"
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center gap-2 cursor-pointer" onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}>
            <div className="w-8 h-8 bg-primary-800 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">AO</span>
            </div>
            <div>
              <span className="font-bold text-slate-900 text-lg leading-none">AO Copilot</span>
              <span className="block text-xs text-slate-500 leading-none">DCE Intelligence</span>
            </div>
          </div>

          {/* Nav links — desktop */}
          <nav className="hidden md:flex items-center gap-6">
            <button onClick={() => scrollTo("features")} className="text-sm text-slate-600 hover:text-primary-800 font-medium transition-colors">
              Fonctionnalités
            </button>
            <button onClick={() => scrollTo("pricing")} className="text-sm text-slate-600 hover:text-primary-800 font-medium transition-colors">
              Tarifs
            </button>
            <button onClick={() => scrollTo("testimonials")} className="text-sm text-slate-600 hover:text-primary-800 font-medium transition-colors">
              Témoignages
            </button>
          </nav>

          {/* CTAs — desktop */}
          <div className="hidden md:flex items-center gap-3">
            <Link
              href="/login"
              className="text-sm font-medium text-primary-800 border border-primary-800 px-4 py-2 rounded-lg hover:bg-primary-50 transition-colors"
            >
              Se connecter
            </Link>
            <Link
              href="/register"
              className="text-sm font-semibold text-white bg-primary-800 px-4 py-2 rounded-lg hover:bg-primary-900 transition-colors shadow-sm"
            >
              Essai 14j gratuit →
            </Link>
          </div>

          {/* Mobile hamburger */}
          <button
            className="md:hidden p-2 rounded-lg text-slate-600 hover:bg-slate-100 transition-colors"
            onClick={() => setMenuOpen((v) => !v)}
            aria-label="Menu"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
              {menuOpen ? (
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
              )}
            </svg>
          </button>
        </div>

        {/* Mobile menu */}
        {menuOpen && (
          <div className="md:hidden border-t border-slate-100 py-4 flex flex-col gap-3">
            <button onClick={() => scrollTo("features")} className="text-sm text-slate-700 font-medium text-left px-1 py-1">Fonctionnalités</button>
            <button onClick={() => scrollTo("pricing")} className="text-sm text-slate-700 font-medium text-left px-1 py-1">Tarifs</button>
            <button onClick={() => scrollTo("testimonials")} className="text-sm text-slate-700 font-medium text-left px-1 py-1">Témoignages</button>
            <hr className="border-slate-100" />
            <Link href="/login" className="text-sm font-medium text-primary-800 border border-primary-800 px-4 py-2 rounded-lg text-center">Se connecter</Link>
            <Link href="/register" className="text-sm font-semibold text-white bg-primary-800 px-4 py-2 rounded-lg text-center">Essai 14j gratuit →</Link>
          </div>
        )}
      </div>
    </header>
  );
}

// --------------------------------------------------------------------------
// Hero mockup — simulated UI screenshot
// --------------------------------------------------------------------------
function MockupUI() {
  return (
    <div className="w-full max-w-2xl mx-auto rounded-2xl shadow-2xl overflow-hidden border border-white/20 bg-white">
      {/* Titlebar */}
      <div className="flex items-center gap-1.5 px-4 py-3 bg-slate-100 border-b border-slate-200">
        <div className="w-3 h-3 rounded-full bg-danger-500 opacity-80" />
        <div className="w-3 h-3 rounded-full bg-warning-500 opacity-80" />
        <div className="w-3 h-3 rounded-full bg-success-500 opacity-80" />
        <div className="flex-1 mx-4 h-5 bg-white rounded border border-slate-200 flex items-center px-3">
          <span className="text-xs text-slate-400">app.ao-copilot.fr/projets/DCE-2024-Lyon</span>
        </div>
      </div>

      {/* Content */}
      <div className="p-5 bg-surface-50">
        {/* Top bar */}
        <div className="flex items-center justify-between mb-4">
          <div>
            <div className="h-4 w-48 bg-slate-200 rounded mb-1" />
            <div className="h-3 w-32 bg-slate-100 rounded" />
          </div>
          <div className="flex gap-2">
            <div className="h-7 w-20 bg-success-100 rounded-full border border-success-200 flex items-center justify-center">
              <span className="text-xs font-semibold text-success-700">GO ✓</span>
            </div>
            <div className="h-7 w-20 bg-primary-100 rounded-full border border-primary-200 flex items-center justify-center">
              <span className="text-xs font-semibold text-primary-700">Score 82</span>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mb-4 border-b border-slate-200">
          {["Résumé", "Checklist", "Critères", "CCAP", "Go/No-Go"].map((t, i) => (
            <div
              key={t}
              className={`px-3 py-1.5 text-xs font-medium rounded-t-md ${
                i === 0
                  ? "bg-primary-800 text-white"
                  : "text-slate-500 hover:text-slate-700"
              }`}
            >
              {t}
            </div>
          ))}
        </div>

        {/* Summary cards */}
        <div className="grid grid-cols-3 gap-3 mb-4">
          {[
            { label: "Points clés", color: "bg-primary-50 border-primary-200", count: 8 },
            { label: "Risques", color: "bg-warning-50 border-warning-200", count: 3 },
            { label: "Actions 48h", color: "bg-danger-50 border-danger-200", count: 2 },
          ].map(({ label, color, count }) => (
            <div key={label} className={`${color} border rounded-xl p-3`}>
              <div className="text-lg font-bold text-slate-800">{count}</div>
              <div className="text-xs text-slate-600">{label}</div>
            </div>
          ))}
        </div>

        {/* Checklist preview */}
        <div className="space-y-2">
          {[
            { text: "Attestation fiscale à jour", status: "ok" },
            { text: "Déclaration sur l'honneur", status: "ok" },
            { text: "CA > 500k€ — délai 5j", status: "warn" },
            { text: "Assurance décennale RC Pro", status: "err" },
          ].map(({ text, status }) => (
            <div key={text} className="flex items-center gap-3 p-2 bg-white rounded-lg border border-slate-100 shadow-sm">
              <div
                className={`w-2 h-2 rounded-full flex-shrink-0 ${
                  status === "ok" ? "bg-success-500" : status === "warn" ? "bg-warning-500" : "bg-danger-500"
                }`}
              />
              <div className="h-3 flex-1 rounded" style={{ background: "#e2e8f0", maxWidth: text.length * 5 }} />
              <span className="text-xs text-slate-400">{text}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// --------------------------------------------------------------------------
// Feature card
// --------------------------------------------------------------------------
interface FeatureCardProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  color: string;
  delay?: number;
}

function FeatureCard({ icon, title, description, color, delay = 0 }: FeatureCardProps) {
  const { ref, visible } = useReveal();
  return (
    <div
      ref={ref}
      className={`bg-white rounded-2xl p-6 shadow-card hover:shadow-card-hover border border-slate-100 transition-all duration-500 ${
        visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-6"
      }`}
      style={{ transitionDelay: `${delay}ms` }}
    >
      <div className={`w-12 h-12 ${color} rounded-xl flex items-center justify-center mb-4`}>{icon}</div>
      <h3 className="font-bold text-slate-900 text-base mb-2">{title}</h3>
      <p className="text-sm text-slate-600 leading-relaxed">{description}</p>
    </div>
  );
}

// --------------------------------------------------------------------------
// Pricing card
// --------------------------------------------------------------------------
interface PricingCardProps {
  name: string;
  price: string;
  period?: string;
  description: string;
  features: string[];
  cta: string;
  popular?: boolean;
  premium?: boolean;
  europe?: boolean;
  business?: boolean;
  delay?: number;
}

function PricingCard({ name, price, period, description, features, cta, popular, premium, europe, business, delay = 0 }: PricingCardProps) {
  const { ref, visible } = useReveal();

  const baseClasses = `relative rounded-2xl p-7 flex flex-col transition-all duration-500 ${
    visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-6"
  }`;

  const styleClasses = business
    ? "bg-gradient-to-br from-amber-900 to-orange-700 text-white shadow-elevation"
    : europe
    ? "bg-gradient-to-br from-purple-900 to-indigo-700 text-white shadow-elevation"
    : premium
    ? "bg-gradient-to-br from-primary-900 to-primary-700 text-white shadow-elevation"
    : popular
    ? "bg-white border-2 border-primary-700 shadow-elevation"
    : "bg-white border border-slate-200 shadow-card";

  const btnClasses = business
    ? "mt-auto w-full py-3 rounded-xl font-semibold text-amber-900 bg-white hover:bg-amber-50 transition-colors text-sm text-center block"
    : europe
    ? "mt-auto w-full py-3 rounded-xl font-semibold text-purple-900 bg-white hover:bg-purple-50 transition-colors text-sm text-center block"
    : premium
    ? "mt-auto w-full py-3 rounded-xl font-semibold text-primary-900 bg-white hover:bg-primary-50 transition-colors text-sm text-center block"
    : popular
    ? "mt-auto w-full py-3 rounded-xl font-semibold text-white bg-primary-800 hover:bg-primary-900 transition-colors text-sm text-center block"
    : "mt-auto w-full py-3 rounded-xl font-semibold text-primary-800 border-2 border-primary-800 hover:bg-primary-50 transition-colors text-sm text-center block";

  const featureColor = (premium || europe || business) ? "text-primary-100" : "text-slate-600";
  const checkColor = business ? "text-amber-200" : europe ? "text-purple-200" : premium ? "text-primary-200" : popular ? "text-primary-700" : "text-primary-600";
  const descColor = (premium || europe || business) ? "text-primary-200" : "text-slate-500";

  return (
    <div ref={ref} className={`${baseClasses} ${styleClasses}`} style={{ transitionDelay: `${delay}ms` }}>
      {(popular || europe || business) && (
        <div className="absolute -top-3.5 left-1/2 -translate-x-1/2">
          <span className={`text-white text-xs font-bold px-4 py-1.5 rounded-full shadow-sm ${
            business ? "bg-gradient-to-r from-amber-600 to-orange-600"
            : europe ? "bg-gradient-to-r from-purple-600 to-indigo-600" : "bg-primary-700"
          }`}>
            {business ? "🏢 Enterprise" : europe ? "🌍 Expansion UE" : "Populaire"}
          </span>
        </div>
      )}

      <div className="mb-6">
        <p className={`text-xs font-semibold uppercase tracking-widest mb-1 ${premium ? "text-primary-200" : "text-slate-400"}`}>{name}</p>
        <div className="flex items-baseline gap-1">
          <span className={`text-4xl font-extrabold ${premium ? "text-white" : "text-slate-900"}`}>{price}</span>
          {period && <span className={`text-sm ${descColor}`}>{period}</span>}
        </div>
        <p className={`text-sm mt-2 ${descColor}`}>{description}</p>
      </div>

      <ul className="space-y-3 mb-7 flex-1">
        {features.map((f) => (
          <li key={f} className="flex items-start gap-2.5">
            <span className={checkColor}><IconCheck /></span>
            <span className={`text-sm ${featureColor}`}>{f}</span>
          </li>
        ))}
      </ul>

      <Link href="/register" className={btnClasses}>{cta}</Link>
    </div>
  );
}

// --------------------------------------------------------------------------
// Testimonial card
// --------------------------------------------------------------------------
interface TestimonialProps {
  quote: string;
  author: string;
  role: string;
  company: string;
  initials: string;
  delay?: number;
}

function TestimonialCard({ quote, author, role, company, initials, delay = 0 }: TestimonialProps) {
  const { ref, visible } = useReveal();
  return (
    <div
      ref={ref}
      className={`bg-white rounded-2xl p-7 shadow-card border border-slate-100 flex flex-col transition-all duration-500 ${
        visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-6"
      }`}
      style={{ transitionDelay: `${delay}ms` }}
    >
      <div className="flex gap-0.5 mb-4">
        {[...Array(5)].map((_, i) => (
          <svg key={i} className="w-4 h-4 text-warning-500" fill="currentColor" viewBox="0 0 20 20">
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
          </svg>
        ))}
      </div>
      <p className="text-slate-700 text-sm leading-relaxed italic flex-1">"{quote}"</p>
      <div className="flex items-center gap-3 mt-6 pt-5 border-t border-slate-100">
        <div className="w-10 h-10 rounded-full bg-primary-100 flex items-center justify-center">
          <span className="text-sm font-bold text-primary-800">{initials}</span>
        </div>
        <div>
          <p className="font-semibold text-slate-900 text-sm">{author}</p>
          <p className="text-xs text-slate-500">{role} · {company}</p>
        </div>
      </div>
    </div>
  );
}

// --------------------------------------------------------------------------
// FAQ accordion item
// --------------------------------------------------------------------------
function FaqItem({ question, answer }: { question: string; answer: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border border-slate-200 rounded-xl overflow-hidden">
      <button
        className="w-full flex items-center justify-between px-6 py-4 text-left bg-white hover:bg-slate-50 transition-colors"
        onClick={() => setOpen((v) => !v)}
      >
        <span className="font-semibold text-slate-800 text-sm pr-4">{question}</span>
        <IconChevron open={open} />
      </button>
      {open && (
        <div className="px-6 pb-5 bg-white">
          <p className="text-sm text-slate-600 leading-relaxed">{answer}</p>
        </div>
      )}
    </div>
  );
}

// --------------------------------------------------------------------------
// Main Landing Page
// --------------------------------------------------------------------------
export default function LandingPage() {
  const heroReveal = useReveal();
  const logosReveal = useReveal();
  const howReveal = useReveal();
  const ctaReveal = useReveal();

  return (
    <div className="min-h-screen font-sans antialiased text-slate-900 bg-white">
      <Navbar />

      {/* ================================================================== */}
      {/* 1. HERO                                                              */}
      {/* ================================================================== */}
      <section className="relative overflow-hidden bg-gradient-to-br from-primary-950 via-primary-900 to-primary-700 text-white pt-32 pb-20 md:pt-36 md:pb-28">
        {/* Background decoration */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-40 -right-40 w-96 h-96 bg-primary-600/20 rounded-full blur-3xl" />
          <div className="absolute -bottom-20 -left-20 w-72 h-72 bg-primary-500/15 rounded-full blur-3xl" />
        </div>

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-4xl mx-auto mb-12">
            {/* Badge */}
            <div
              ref={heroReveal.ref}
              className={`inline-flex items-center gap-2 bg-white/10 backdrop-blur-sm border border-white/20 rounded-full px-4 py-1.5 mb-6 transition-all duration-700 ${
                heroReveal.visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
              }`}
            >
              <span className="text-sm">🚀</span>
              <span className="text-sm font-medium text-primary-100">Aucune carte bancaire requise</span>
            </div>

            {/* H1 */}
            <h1
              className={`text-4xl md:text-5xl lg:text-6xl font-extrabold leading-tight mb-6 transition-all duration-700 delay-100 ${
                heroReveal.visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
              }`}
            >
              Analysez vos DCE
              <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-200 to-white">
                en 5 minutes chrono
              </span>
            </h1>

            {/* Subtitle */}
            <p
              className={`text-lg md:text-xl text-primary-100 max-w-2xl mx-auto mb-8 leading-relaxed transition-all duration-700 delay-200 ${
                heroReveal.visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
              }`}
            >
              L'IA qui décrypte vos Appels d'Offres BTP : checklist conformité, risques CCAP, score Go/No-Go et Mémoire Technique en un clic.
            </p>

            {/* CTAs */}
            <div
              className={`flex flex-col sm:flex-row gap-3 justify-center mb-12 transition-all duration-700 delay-300 ${
                heroReveal.visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
              }`}
            >
              <Link
                href="/register"
                className="inline-flex items-center justify-center gap-2 bg-white text-primary-900 font-bold px-7 py-3.5 rounded-xl hover:bg-primary-50 transition-colors shadow-lg text-base"
              >
                Démarrer l'essai gratuit
                <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2.5} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
                </svg>
              </Link>
              <button
                onClick={() => document.getElementById("features")?.scrollIntoView({ behavior: "smooth" })}
                className="inline-flex items-center justify-center gap-2 border-2 border-white/40 text-white font-semibold px-7 py-3.5 rounded-xl hover:bg-white/10 hover:border-white/60 transition-colors text-base"
              >
                Voir la démo →
              </button>
            </div>

            {/* Pricing tiers inline */}
            <div
              className={`flex flex-wrap items-center justify-center gap-3 sm:gap-4 transition-all duration-700 delay-350 ${
                heroReveal.visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
              }`}
            >
              {[
                { name: "Gratuit", price: "0€" },
                { name: "Starter", price: "69€" },
                { name: "Pro", price: "179€" },
                { name: "Europe", price: "299€" },
                { name: "Business", price: "499€", highlight: true },
              ].map(({ name, price, highlight }) => (
                <button
                  key={name}
                  onClick={() => document.getElementById("pricing")?.scrollIntoView({ behavior: "smooth" })}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium transition-colors cursor-pointer ${
                    highlight
                      ? "bg-amber-500/20 border border-amber-400/40 text-amber-200 hover:bg-amber-500/30"
                      : "bg-white/10 border border-white/20 text-primary-100 hover:bg-white/20"
                  }`}
                >
                  <span>{name}</span>
                  <span className={`font-bold ${highlight ? "text-amber-300" : "text-white"}`}>{price}</span>
                  <span className="text-primary-300 text-xs">/mois</span>
                </button>
              ))}
            </div>
          </div>

          {/* Stats row */}
          <div
            className={`flex flex-col sm:flex-row items-center justify-center gap-6 sm:gap-10 mb-14 transition-all duration-700 delay-400 ${
              heroReveal.visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
            }`}
          >
            {[
              { value: "500+", label: "entreprises BTP" },
              { value: "50 000+", label: "DCE analysés" },
              { value: "5 min", label: "analyse moyenne" },
            ].map(({ value, label }) => (
              <div key={label} className="text-center">
                <div className="text-2xl font-extrabold text-white">{value}</div>
                <div className="text-sm text-primary-200">{label}</div>
              </div>
            ))}
          </div>

          {/* Mockup */}
          <div
            className={`transition-all duration-1000 delay-500 ${
              heroReveal.visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-10"
            }`}
          >
            <MockupUI />
          </div>
        </div>
      </section>

      {/* ================================================================== */}
      {/* 2. LOGOS CLIENTS                                                     */}
      {/* ================================================================== */}
      <section className="py-14 bg-surface-100 border-y border-slate-200">
        <div
          ref={logosReveal.ref}
          className={`max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 transition-all duration-700 ${
            logosReveal.visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-6"
          }`}
        >
          <p className="text-center text-xs font-semibold uppercase tracking-widest text-slate-400 mb-8">
            Approuvé par les entreprises BTP françaises
          </p>
          <div className="flex flex-wrap items-center justify-center gap-x-10 gap-y-5">
            {["Artelia", "Eiffage TP", "Spie Batignolles", "NGE", "Colas", "Egis"].map((name) => (
              <div key={name} className="text-slate-400 font-bold text-lg tracking-tight hover:text-slate-500 transition-colors cursor-default select-none">
                {name}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ================================================================== */}
      {/* 3. FEATURES                                                          */}
      {/* ================================================================== */}
      <section id="features" className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-14">
            <span className="inline-block bg-primary-50 text-primary-800 text-xs font-semibold uppercase tracking-widest px-3 py-1 rounded-full mb-3">
              Fonctionnalités
            </span>
            <h2 className="text-3xl md:text-4xl font-extrabold text-slate-900 mb-4">
              Tout pour gagner vos appels d'offres
            </h2>
            <p className="text-slate-500 max-w-xl mx-auto text-base">
              De l'analyse automatique à l'export final, AO Copilot couvre l'intégralité de votre processus de réponse DCE.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <FeatureCard
              icon={<IconBrain />}
              title="Analyse IA complète"
              description="Claude IA décrypte l'intégralité de votre DCE : résumé exécutif, points clés, risques identifiés et actions prioritaires sous 5 minutes."
              color="bg-primary-50 text-primary-700"
              delay={0}
            />
            <FeatureCard
              icon={<IconShield />}
              title="Risques CCAP détectés"
              description="L'IA identifie automatiquement les clauses abusives, délais contractuels piégés et pénalités excessives dans votre CCAP."
              color="bg-danger-50 text-danger-600"
              delay={80}
            />
            <FeatureCard
              icon={<IconGoNoGo />}
              title="Score Go/No-Go"
              description="Obtenez un score de pertinence sur 100 basé sur votre profil entreprise, vos capacités et les exigences du lot. Décidez en 2 minutes."
              color="bg-success-50 text-success-700"
              delay={160}
            />
            <FeatureCard
              icon={<IconDoc />}
              title="Mémoire Technique IA"
              description="Générez une mémoire technique structurée Word, adaptée aux exigences du RC, réutilisant votre bibliothèque de réponses BTP."
              color="bg-warning-50 text-warning-600"
              delay={240}
            />
            <FeatureCard
              icon={<IconExcel />}
              title="Export DPGF / BPU Excel"
              description="Extraction automatique des postes DPGF et BPU dans un fichier Excel prêt à chiffrer — plus aucune saisie manuelle."
              color="bg-success-50 text-success-700"
              delay={320}
            />
            <FeatureCard
              icon={<IconBell />}
              title="Veille BOAMP automatique"
              description="Soyez alerté dès qu'un appel d'offres correspondant à votre métier et région est publié au BOAMP. Ne ratez plus aucune opportunité."
              color="bg-primary-50 text-primary-700"
              delay={400}
            />
          </div>
        </div>
      </section>

      {/* ================================================================== */}
      {/* 4. HOW IT WORKS                                                      */}
      {/* ================================================================== */}
      <section className="py-24 bg-primary-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-14">
            <span className="inline-block bg-primary-100 text-primary-800 text-xs font-semibold uppercase tracking-widest px-3 py-1 rounded-full mb-3">
              Comment ça marche
            </span>
            <h2 className="text-3xl md:text-4xl font-extrabold text-slate-900 mb-4">
              3 étapes, 5 minutes, résultat clé en main
            </h2>
          </div>

          <div
            ref={howReveal.ref}
            className="grid grid-cols-1 md:grid-cols-3 gap-8"
          >
            {[
              {
                step: "01",
                title: "Déposez vos documents DCE",
                description: "Glissez-déposez vos PDFs, DOCX ou images (RC, CCTP, CCAP, DPGF...). AO Copilot reconnaît automatiquement chaque type de pièce.",
                icon: "📁",
              },
              {
                step: "02",
                title: "L'IA analyse et structure",
                description: "Notre pipeline IA (OCR + embeddings + Claude) traite chaque document, extrait les informations clés et génère checklist, risques et score Go/No-Go.",
                icon: "⚙️",
              },
              {
                step: "03",
                title: "Exportez et répondez",
                description: "Téléchargez votre rapport PDF, votre Mémoire Technique Word et votre DPGF Excel. Votre équipe collabore en temps réel sur les annotations.",
                icon: "📤",
              },
            ].map(({ step, title, description, icon }, i) => (
              <div
                key={step}
                className={`relative bg-white rounded-2xl p-8 shadow-card border border-primary-100 transition-all duration-700 ${
                  howReveal.visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
                }`}
                style={{ transitionDelay: `${i * 120}ms` }}
              >
                {/* Connector line */}
                {i < 2 && (
                  <div className="hidden md:block absolute top-1/2 -right-4 w-8 h-px bg-primary-200 z-10" />
                )}
                <div className="text-3xl mb-4">{icon}</div>
                <div className="inline-block bg-primary-800 text-white text-xs font-bold px-3 py-1 rounded-full mb-3">
                  Étape {step}
                </div>
                <h3 className="font-bold text-slate-900 text-base mb-2">{title}</h3>
                <p className="text-sm text-slate-600 leading-relaxed">{description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ================================================================== */}
      {/* 5. PRICING                                                           */}
      {/* ================================================================== */}
      <section id="pricing" className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-6">
            <span className="inline-block bg-primary-50 text-primary-800 text-xs font-semibold uppercase tracking-widest px-3 py-1 rounded-full mb-3">
              Tarifs transparents
            </span>
            <h2 className="text-3xl md:text-4xl font-extrabold text-slate-900 mb-4">
              Un plan pour chaque équipe BTP
            </h2>
            <p className="text-slate-500 text-base">Sans engagement, résiliable à tout moment.</p>
          </div>

          {/* Promo banner */}
          <div className="flex justify-center mb-10">
            <div className="inline-flex items-center gap-2 bg-warning-50 border border-warning-200 text-warning-700 text-sm font-semibold px-5 py-2.5 rounded-full shadow-sm">
              <span>⭐</span>
              <span>Essai 14 jours gratuit inclus — sans CB, sans engagement</span>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-5 items-start">
            <PricingCard
              name="Gratuit"
              price="0€"
              period="/mois"
              description="Pour découvrir AO Copilot sans risque."
              features={[
                "1 utilisateur",
                "5 DCE / mois",
                "Analyse IA basique (résumé)",
                "Checklist conformité",
                "Export PDF",
                "Rétention 14 jours",
              ]}
              cta="Commencer gratuitement"
              delay={0}
            />
            <PricingCard
              name="Starter"
              price="69€"
              period="/mois HT"
              description="Pour les PME BTP qui répondent régulièrement aux AO."
              features={[
                "1 utilisateur",
                "15 DCE / mois",
                "Analyse IA complète",
                "Risques CCAP détaillés",
                "Score Go/No-Go avancé",
                "Export PDF + Word",
                "Rétention 30 jours",
                "Support email prioritaire",
              ]}
              cta="Choisir Starter"
              popular
              delay={100}
            />
            <PricingCard
              name="Pro"
              price="179€"
              period="/mois HT"
              description="Pour les équipes qui veulent tout automatiser."
              features={[
                "5 utilisateurs inclus",
                "60 DCE / mois",
                "Tout Starter +",
                "Mémoire Technique Word IA",
                "Export DPGF / BPU Excel",
                "Veille BOAMP automatique",
                "Bibliothèque réponses",
                "Annotations équipe",
                "Rétention 90 jours",
                "Support dédié",
              ]}
              cta="Choisir Pro"
              premium
              delay={200}
            />
            <PricingCard
              name="Europe"
              price="299€"
              period="/mois HT"
              description="Marchés UE : Wallonie, Luxembourg, TED."
              features={[
                "20 utilisateurs inclus",
                "100 DCE / mois",
                "Tout Pro +",
                "Monitoring TED (UE)",
                "Marchés Wallonie & Luxembourg",
                "Analyse bilingue FR/EN",
                "Rétention 180 jours",
                "Support prioritaire dédié",
              ]}
              cta="Contactez-nous"
              europe
              delay={300}
            />
            <PricingCard
              name="Business"
              price="499€"
              period="/mois HT"
              description="SSO, SLA 99.9%, API & volume illimité."
              features={[
                "Utilisateurs illimités",
                "Documents illimités",
                "Tout Europe +",
                "SSO SAML",
                "SLA 99.9%",
                "API & Webhooks",
                "Onboarding dédié",
                "Support prioritaire 24/7",
              ]}
              cta="Demander un devis"
              business
              delay={400}
            />
          </div>

          <p className="text-center mt-8 text-sm text-slate-500">
            Tous les plans payants : <strong>-20% en facturation annuelle</strong>.{" "}
            Paiement à l&apos;usage aussi disponible : <strong>3€/document</strong>.
          </p>
        </div>
      </section>

      {/* ================================================================== */}
      {/* 6. TESTIMONIALS                                                      */}
      {/* ================================================================== */}
      <section id="testimonials" className="py-24 bg-surface-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-14">
            <span className="inline-block bg-primary-50 text-primary-800 text-xs font-semibold uppercase tracking-widest px-3 py-1 rounded-full mb-3">
              Témoignages
            </span>
            <h2 className="text-3xl md:text-4xl font-extrabold text-slate-900 mb-4">
              Ce que disent nos clients
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <TestimonialCard
              quote="On analyse 3x plus de DCE par semaine depuis qu'on utilise AO Copilot. La détection des clauses CCAP risquées nous a évité un vrai piège contractuel sur un chantier en Île-de-France."
              author="Sophie Marchand"
              role="Responsable Appels d'Offres"
              company="Groupe Lefeuvre TP"
              initials="SM"
              delay={0}
            />
            <TestimonialCard
              quote="Le score Go/No-Go nous fait gagner un temps précieux. En 5 minutes on sait si ça vaut le coup de répondre. Notre taux de succès a progressé de 18 points en 6 mois."
              author="Julien Beaumont"
              role="Directeur Commercial"
              company="ICEA Ingénierie"
              initials="JB"
              delay={100}
            />
            <TestimonialCard
              quote="La génération automatique de la Mémoire Technique est bluffante. Elle reprend nos références passées et les adapte au lot. Notre chef de projet a divisé son temps de rédaction par 4."
              author="Nathalie Girard"
              role="Chargée d'Affaires"
              company="Bâtiplan Construction"
              initials="NG"
              delay={200}
            />
          </div>
        </div>
      </section>

      {/* ================================================================== */}
      {/* 7. FAQ                                                               */}
      {/* ================================================================== */}
      <section className="py-24 bg-white">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <span className="inline-block bg-primary-50 text-primary-800 text-xs font-semibold uppercase tracking-widest px-3 py-1 rounded-full mb-3">
              FAQ
            </span>
            <h2 className="text-3xl md:text-4xl font-extrabold text-slate-900">
              Questions fréquentes
            </h2>
          </div>

          <div className="space-y-3">
            <FaqItem
              question="Mes documents sont-ils sécurisés et confidentiels ?"
              answer="Absolument. AO Copilot est hébergé exclusivement en France (Scaleway Paris PAR1), conforme RGPD. Vos DCE sont chiffrés au repos et en transit. Chaque entreprise dispose d'un espace totalement isolé (Row-Level Security). Nous ne partageons jamais vos données avec des tiers et nous ne les utilisons pas pour entraîner des modèles IA."
            />
            <FaqItem
              question="Quels formats de documents puis-je importer ?"
              answer="AO Copilot accepte les PDFs natifs et scannés (avec OCR automatique via Tesseract), les fichiers DOCX, ainsi que les images JPEG, PNG et TIFF. Le système détecte automatiquement le type de pièce : RC, CCTP, CCAP, DPGF, BPU, AE, ATTRI."
            />
            <FaqItem
              question="L'IA est-elle fiable sur des documents techniques BTP ?"
              answer="Oui. Notre modèle est spécialisé BTP grâce à un corpus de connaissances métier (normes, textes réglementaires, terminologie CCAG). Chaque information extraite est accompagnée d'un score de confiance et d'une citation source dans le document original. En cas de doute, le système vous invite à vérifier manuellement."
            />
            <FaqItem
              question="Puis-je essayer sans carte bancaire ?"
              answer="Oui. L'essai 14 jours gratuit ne nécessite aucune carte bancaire, aucun engagement. Vous accédez à l'ensemble des fonctionnalités Pro pendant 14 jours. À l'issue de l'essai, vous choisissez librement votre plan ou vous arrêtez — sans frais."
            />
            <FaqItem
              question="Comment fonctionne la collaboration en équipe ?"
              answer="Avec le plan Pro, vous pouvez inviter jusqu'à 5 collaborateurs. Chaque membre peut annoter les checklists, commenter les risques et co-éditer les réponses. Un pipeline Kanban multi-projets vous permet de suivre l'avancement de toutes vos réponses en cours en un coup d'oeil."
            />
          </div>
        </div>
      </section>

      {/* ================================================================== */}
      {/* 8. FINAL CTA BANNER                                                  */}
      {/* ================================================================== */}
      <section className="py-20 bg-gradient-to-br from-primary-900 to-primary-700 text-white">
        <div
          ref={ctaReveal.ref}
          className={`max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center transition-all duration-700 ${
            ctaReveal.visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-6"
          }`}
        >
          <h2 className="text-3xl md:text-4xl font-extrabold mb-5 leading-tight">
            Prêt à gagner plus d'appels d'offres ?
          </h2>
          <p className="text-primary-100 text-lg mb-8 max-w-2xl mx-auto">
            Rejoignez 500+ entreprises BTP qui font confiance à AO Copilot pour analyser leurs DCE plus vite et répondre plus juste.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/register"
              className="inline-flex items-center justify-center gap-2 bg-white text-primary-900 font-bold px-8 py-4 rounded-xl hover:bg-primary-50 transition-colors shadow-lg text-base"
            >
              Commencer l'essai gratuit — 14j sans CB
              <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2.5} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
              </svg>
            </Link>
            <a
              href="mailto:contact@ao-copilot.fr"
              className="inline-flex items-center justify-center gap-2 border-2 border-white/40 text-white font-semibold px-8 py-4 rounded-xl hover:bg-white/10 transition-colors text-base"
            >
              Nous contacter
            </a>
          </div>
          <p className="mt-5 text-primary-200 text-sm">Sans engagement · Résiliable à tout moment · Hébergé en France</p>
        </div>
      </section>

      {/* ================================================================== */}
      {/* 9. FOOTER                                                            */}
      {/* ================================================================== */}
      <footer className="bg-slate-900 text-slate-400">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-14">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-10 mb-10">
            {/* Brand */}
            <div className="md:col-span-2">
              <div className="flex items-center gap-2 mb-3">
                <div className="w-8 h-8 bg-primary-700 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">AO</span>
                </div>
                <span className="font-bold text-white text-lg">AO Copilot</span>
              </div>
              <p className="text-sm leading-relaxed max-w-xs">
                L'assistant IA de référence pour l'analyse de DCE en France. Conçu pour les entreprises BTP et d'ingénierie.
              </p>
              <div className="mt-4 inline-flex items-center gap-1.5 bg-slate-800 border border-slate-700 rounded-full px-3 py-1.5 text-xs">
                <span>🇫🇷</span>
                <span>Hébergé en France · RGPD</span>
              </div>
            </div>

            {/* Produit */}
            <div>
              <h4 className="text-white font-semibold text-sm mb-4">Produit</h4>
              <ul className="space-y-2.5 text-sm">
                <li><button onClick={() => document.getElementById("features")?.scrollIntoView({ behavior: "smooth" })} className="hover:text-white transition-colors">Fonctionnalités</button></li>
                <li><button onClick={() => document.getElementById("pricing")?.scrollIntoView({ behavior: "smooth" })} className="hover:text-white transition-colors">Tarifs</button></li>
                <li><button onClick={() => document.getElementById("testimonials")?.scrollIntoView({ behavior: "smooth" })} className="hover:text-white transition-colors">Témoignages</button></li>
                <li><Link href="/login" className="hover:text-white transition-colors">Connexion</Link></li>
                <li><Link href="/register" className="hover:text-white transition-colors">Essai gratuit</Link></li>
              </ul>
            </div>

            {/* Légal */}
            <div>
              <h4 className="text-white font-semibold text-sm mb-4">Légal</h4>
              <ul className="space-y-2.5 text-sm">
                <li><Link href="/legal/mentions-legales" className="hover:text-white transition-colors">Mentions légales</Link></li>
                <li><Link href="/legal/cgu" className="hover:text-white transition-colors">Conditions générales</Link></li>
                <li><Link href="/legal/confidentialite" className="hover:text-white transition-colors">Politique de confidentialité</Link></li>
                <li>
                  <a href="mailto:contact@ao-copilot.fr" className="hover:text-white transition-colors">
                    contact@ao-copilot.fr
                  </a>
                </li>
              </ul>
            </div>
          </div>

          <div className="border-t border-slate-800 pt-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs">
            <p>© {new Date().getFullYear()} AO Copilot — Tous droits réservés</p>
            <p className="text-slate-500">Hébergé en France 🇫🇷 · Conforme RGPD · Données non partagées</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
