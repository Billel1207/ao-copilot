"use client";

export const dynamic = "force-dynamic";

import { useState, useEffect, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search, BookOpen, Scale, Award, ChevronRight } from "lucide-react";
import api from "@/lib/api";

// ── Types ──────────────────────────────────────────────────────────────────

interface GlossaryTerm {
  term: string;
  definition: string;
}

interface Threshold {
  montant_ht?: number;
  montant_ht_min?: number;
  montant_ht_max_travaux?: number;
  montant_ht_max_services_fournitures?: number;
  label: string;
  description: string;
  taux?: string;
  jours?: number;
}

interface Certification {
  name: string;
  description: string;
}

// ── API Fetchers ───────────────────────────────────────────────────────────

const fetchGlossary = async (): Promise<GlossaryTerm[]> => {
  const res = await api.get<{ terms: GlossaryTerm[] }>("/knowledge/glossary");
  return res.data.terms;
};

const fetchThresholds = async (): Promise<Record<string, Threshold>> => {
  const res = await api.get<{ thresholds: Record<string, Threshold> }>("/knowledge/thresholds");
  return res.data.thresholds;
};

const fetchCertifications = async (): Promise<Certification[]> => {
  const res = await api.get<{ certifications: Certification[] }>("/knowledge/certifications");
  return res.data.certifications;
};

// ── Composants ─────────────────────────────────────────────────────────────

function SectionTitle({ icon, title, count }: { icon: React.ReactNode; title: string; count?: number }) {
  return (
    <div className="flex items-center gap-3 mb-6">
      <div className="p-2 rounded-xl bg-blue-50 text-blue-700">{icon}</div>
      <div>
        <h2 className="text-lg font-bold text-gray-900">{title}</h2>
        {count !== undefined && (
          <p className="text-xs text-gray-400">{count} entrée{count > 1 ? "s" : ""}</p>
        )}
      </div>
    </div>
  );
}

function TermCard({ term, definition }: GlossaryTerm) {
  return (
    <div className="bg-white border border-gray-100 rounded-xl p-4 shadow-sm hover:shadow-md hover:border-blue-200 transition-all duration-150">
      <div className="flex items-start gap-3">
        <ChevronRight className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
        <div>
          <p className="font-semibold text-gray-900 text-sm">{term}</p>
          <p className="text-xs text-gray-500 mt-1 leading-relaxed">{definition}</p>
        </div>
      </div>
    </div>
  );
}

function AlphaIndex({
  letters,
  active,
  onSelect,
}: {
  letters: string[];
  active: string | null;
  onSelect: (letter: string | null) => void;
}) {
  const all = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");
  return (
    <div className="flex flex-wrap gap-1 mb-6">
      <button
        onClick={() => onSelect(null)}
        className={`px-2 py-1 rounded text-xs font-semibold transition-colors duration-100
          ${active === null ? "bg-blue-700 text-white" : "bg-gray-100 text-gray-500 hover:bg-blue-50 hover:text-blue-700"}`}
      >
        Tous
      </button>
      {all.map((letter) => {
        const available = letters.includes(letter);
        const isActive = active === letter;
        return (
          <button
            key={letter}
            onClick={() => available && onSelect(isActive ? null : letter)}
            disabled={!available}
            className={`w-7 h-7 rounded text-xs font-bold transition-colors duration-100
              ${isActive
                ? "bg-blue-700 text-white"
                : available
                  ? "bg-gray-100 text-gray-700 hover:bg-blue-50 hover:text-blue-700"
                  : "bg-gray-50 text-gray-300 cursor-not-allowed"}`}
          >
            {letter}
          </button>
        );
      })}
    </div>
  );
}

function ThresholdsTable({ thresholds }: { thresholds: Record<string, Threshold> }) {
  const rows = Object.entries(thresholds).map(([key, val]) => {
    let montant = "";
    if (val.montant_ht !== undefined) {
      montant = `${val.montant_ht.toLocaleString("fr-FR")} € HT`;
    } else if (val.montant_ht_max_travaux !== undefined) {
      montant = `Jusqu'à ${val.montant_ht_max_travaux.toLocaleString("fr-FR")} € HT (travaux)`;
    } else if (val.taux) {
      montant = val.taux;
    } else if (val.jours !== undefined) {
      montant = `${val.jours} jours`;
    }
    return { key, label: val.label, montant, description: val.description };
  });

  return (
    <div className="overflow-hidden border border-gray-200 rounded-xl">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 border-b border-gray-200">
          <tr>
            <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
              Seuil / Règle
            </th>
            <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
              Valeur
            </th>
            <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide hidden md:table-cell">
              Description
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {rows.map(({ key, label, montant, description }) => (
            <tr key={key} className="hover:bg-blue-50/30 transition-colors">
              <td className="px-4 py-3">
                <span className="font-semibold text-gray-800">{label}</span>
              </td>
              <td className="px-4 py-3">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  {montant}
                </span>
              </td>
              <td className="px-4 py-3 text-gray-500 text-xs hidden md:table-cell max-w-xs">
                {description}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function CertificationGrid({ certs }: { certs: Certification[] }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
      {certs.map(({ name, description }) => (
        <div
          key={name}
          className="bg-white border border-gray-100 rounded-xl p-4 shadow-sm hover:border-green-200 hover:shadow-md transition-all duration-150"
        >
          <div className="flex items-center gap-2 mb-2">
            <div className="w-2 h-2 rounded-full bg-green-500 flex-shrink-0" />
            <p className="font-semibold text-gray-900 text-sm">{name}</p>
          </div>
          <p className="text-xs text-gray-500 leading-relaxed">{description}</p>
        </div>
      ))}
    </div>
  );
}

// ── Page principale ────────────────────────────────────────────────────────

type Section = "glossaire" | "seuils" | "certifications";

export default function GlossairePage() {
  const [search, setSearch] = useState("");
  const [activeLetter, setActiveLetter] = useState<string | null>(null);
  const [activeSection, setActiveSection] = useState<Section>("glossaire");

  const { data: terms = [], isLoading: loadingTerms } = useQuery({
    queryKey: ["knowledge", "glossary"],
    queryFn: fetchGlossary,
    staleTime: 10 * 60 * 1000,
  });

  const { data: thresholds, isLoading: loadingThresholds } = useQuery({
    queryKey: ["knowledge", "thresholds"],
    queryFn: fetchThresholds,
    staleTime: 30 * 60 * 1000,
  });

  const { data: certifications = [], isLoading: loadingCerts } = useQuery({
    queryKey: ["knowledge", "certifications"],
    queryFn: fetchCertifications,
    staleTime: 30 * 60 * 1000,
  });

  // Index alphabétique disponible
  const availableLetters = useMemo(() => {
    const letters = new Set<string>();
    terms.forEach((t) => {
      const first = t.term[0]?.toUpperCase();
      if (first && /[A-Z]/.test(first)) letters.add(first);
    });
    return Array.from(letters).sort();
  }, [terms]);

  // Filtrage des termes
  const filteredTerms = useMemo(() => {
    let result = terms;
    if (activeLetter) {
      result = result.filter((t) => t.term[0]?.toUpperCase() === activeLetter);
    }
    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter(
        (t) =>
          t.term.toLowerCase().includes(q) ||
          t.definition.toLowerCase().includes(q)
      );
    }
    return result;
  }, [terms, activeLetter, search]);

  const tabs: { key: Section; label: string; icon: React.ReactNode }[] = [
    { key: "glossaire", label: "Glossaire BTP", icon: <BookOpen className="w-4 h-4" /> },
    { key: "seuils", label: "Seuils réglementaires", icon: <Scale className="w-4 h-4" /> },
    { key: "certifications", label: "Certifications", icon: <Award className="w-4 h-4" /> },
  ];

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-8 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Référentiel BTP</h1>
        <p className="text-gray-500 mt-1 text-sm">
          Base de connaissances BTP/marchés publics — glossaire, seuils réglementaires 2024,
          certifications et qualifications.
        </p>
      </div>

      {/* Navigation par sections */}
      <div className="flex gap-1 p-1 bg-gray-100 rounded-xl w-fit">
        {tabs.map(({ key, label, icon }) => (
          <button
            key={key}
            onClick={() => setActiveSection(key)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-150
              ${activeSection === key
                ? "bg-white text-blue-700 shadow-sm"
                : "text-gray-500 hover:text-gray-800"}`}
          >
            {icon}
            {label}
          </button>
        ))}
      </div>

      {/* SECTION GLOSSAIRE */}
      {activeSection === "glossaire" && (
        <div className="space-y-6">
          <SectionTitle
            icon={<BookOpen className="w-5 h-5" />}
            title="Glossaire BTP & Marchés Publics"
            count={terms.length}
          />

          {/* Barre de recherche */}
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setActiveLetter(null);
              }}
              placeholder="Rechercher un terme ou une définition..."
              className="w-full pl-9 pr-4 py-2.5 text-sm border border-gray-200 rounded-xl focus:outline-none
                focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white shadow-sm"
            />
          </div>

          {/* Index alphabétique */}
          {!search && (
            <AlphaIndex
              letters={availableLetters}
              active={activeLetter}
              onSelect={setActiveLetter}
            />
          )}

          {/* Résultats */}
          {loadingTerms ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {Array.from({ length: 8 }).map((_, i) => (
                <div key={i} className="h-20 bg-gray-100 rounded-xl animate-pulse" />
              ))}
            </div>
          ) : filteredTerms.length === 0 ? (
            <div className="text-center py-16 text-gray-400">
              <BookOpen className="w-10 h-10 mx-auto mb-3 text-gray-300" />
              <p className="font-medium text-gray-600">Aucun terme trouvé</p>
              <p className="text-sm mt-1">Essayez un autre terme ou effacez la recherche.</p>
            </div>
          ) : (
            <>
              <p className="text-xs text-gray-400">
                {filteredTerms.length} terme{filteredTerms.length > 1 ? "s" : ""}
                {activeLetter ? ` commençant par ${activeLetter}` : ""}
                {search ? ` contenant "${search}"` : ""}
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {filteredTerms.map((t) => (
                  <TermCard key={t.term} term={t.term} definition={t.definition} />
                ))}
              </div>
            </>
          )}
        </div>
      )}

      {/* SECTION SEUILS REGLEMENTAIRES */}
      {activeSection === "seuils" && (
        <div className="space-y-6">
          <SectionTitle
            icon={<Scale className="w-5 h-5" />}
            title="Seuils Reglementaires Marchés Publics 2024"
          />

          <div className="bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 text-sm text-amber-800">
            <strong>Note :</strong> Les seuils européens sont révisés tous les 2 ans (prochain ajustement 2026).
            Les montants indiqués sont en euros HT et s'appliquent aux marchés publics français.
          </div>

          {loadingThresholds ? (
            <div className="space-y-2">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="h-12 bg-gray-100 rounded-xl animate-pulse" />
              ))}
            </div>
          ) : thresholds ? (
            <ThresholdsTable thresholds={thresholds} />
          ) : (
            <p className="text-gray-400 text-sm">Impossible de charger les seuils.</p>
          )}

          {/* Aide rapide */}
          <div className="bg-blue-50 border border-blue-200 rounded-xl p-5">
            <h3 className="font-semibold text-blue-900 mb-3 text-sm">Guide rapide — quelle procédure ?</h3>
            <div className="space-y-2">
              {[
                { montant: "< 25 000 € HT", procedure: "Gré à gré", color: "text-green-700" },
                { montant: "25 000 € — 221 000 € HT", procedure: "MAPA (Marché à Procédure Adaptée)", color: "text-blue-700" },
                { montant: "221 000 € — 5 382 000 € HT", procedure: "Procédure formalisée — Services/Fournitures", color: "text-amber-700" },
                { montant: "> 5 382 000 € HT", procedure: "Appel d'offres formalisé — Travaux", color: "text-red-700" },
              ].map(({ montant, procedure, color }) => (
                <div key={montant} className="flex items-center gap-3 text-sm">
                  <span className="font-mono text-xs bg-white border border-blue-200 px-2 py-0.5 rounded text-gray-700 flex-shrink-0">
                    {montant}
                  </span>
                  <ChevronRight className="w-3 h-3 text-gray-400 flex-shrink-0" />
                  <span className={`font-medium ${color}`}>{procedure}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* SECTION CERTIFICATIONS */}
      {activeSection === "certifications" && (
        <div className="space-y-6">
          <SectionTitle
            icon={<Award className="w-5 h-5" />}
            title="Certifications & Qualifications BTP"
            count={certifications.length}
          />

          <p className="text-sm text-gray-500">
            Les certifications et qualifications attestent des compétences techniques, financières
            et organisationnelles des entreprises. Elles sont fréquemment exigées dans les DCE.
          </p>

          {loadingCerts ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {Array.from({ length: 9 }).map((_, i) => (
                <div key={i} className="h-24 bg-gray-100 rounded-xl animate-pulse" />
              ))}
            </div>
          ) : (
            <CertificationGrid certs={certifications} />
          )}

          {/* Note sur RGE */}
          <div className="bg-green-50 border border-green-200 rounded-xl px-4 py-3 text-sm text-green-800">
            <strong>RGE :</strong> La mention "Reconnu Garant de l'Environnement" est obligatoire
            pour que vos clients particuliers puissent bénéficier des aides financières
            (MaPrimeRénov', CEE). Vérifier le champ de qualification correspondant à votre activité.
          </div>
        </div>
      )}
    </div>
  );
}
