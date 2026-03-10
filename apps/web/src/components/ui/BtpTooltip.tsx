"use client";

import { useState, useRef, useEffect } from "react";

const BTP_TERMS: Record<string, string> = {
  BFR: "Besoin en Fonds de Roulement \u2014 capital n\u00e9cessaire pour couvrir le d\u00e9calage entre d\u00e9penses (mat\u00e9riaux, MO) et encaissements (situations pay\u00e9es).",
  GPA: "Garantie de Parfait Ach\u00e8vement \u2014 1 an apr\u00e8s r\u00e9ception, obligation de r\u00e9parer tous les d\u00e9sordres signal\u00e9s (CCAG Art. 44).",
  CCAG: "Cahier des Clauses Administratives G\u00e9n\u00e9rales \u2014 r\u00e8gles contractuelles standard des march\u00e9s publics (version Travaux 2021).",
  CCAP: "Cahier des Clauses Administratives Particuli\u00e8res \u2014 clauses sp\u00e9cifiques au march\u00e9 qui compl\u00e8tent ou d\u00e9rogent au CCAG.",
  CCTP: "Cahier des Clauses Techniques Particuli\u00e8res \u2014 sp\u00e9cifications techniques d\u00e9taill\u00e9es de l'ouvrage (mat\u00e9riaux, normes, essais).",
  DPGF: "D\u00e9composition du Prix Global et Forfaitaire \u2014 d\u00e9tail des prix unitaires composant le montant global du march\u00e9.",
  BPU: "Bordereau des Prix Unitaires \u2014 liste des prix unitaires par poste, utilis\u00e9 pour les march\u00e9s \u00e0 bons de commande.",
  DCE: "Dossier de Consultation des Entreprises \u2014 ensemble des pi\u00e8ces du march\u00e9 (RC, CCAP, CCTP, DPGF, AE, plans).",
  RC: "R\u00e8glement de la Consultation \u2014 r\u00e8gles de la proc\u00e9dure (crit\u00e8res de jugement, modalit\u00e9s de remise, pi\u00e8ces exig\u00e9es).",
  AE: "Acte d'Engagement \u2014 pi\u00e8ce sign\u00e9e par le candidat avec le montant, la dur\u00e9e et les conditions financi\u00e8res du march\u00e9.",
  DOE: "Dossier des Ouvrages Ex\u00e9cut\u00e9s \u2014 documentation technique remise apr\u00e8s travaux (plans conformes, notices, PV essais).",
  DIUO: "Dossier d'Interventions Ult\u00e9rieures sur l'Ouvrage \u2014 consignes de s\u00e9curit\u00e9 pour la maintenance future.",
  DTU: "Document Technique Unifi\u00e9 \u2014 norme fran\u00e7aise NF DTU d\u00e9finissant les r\u00e8gles de l'art pour chaque corps de m\u00e9tier.",
  "RE 2020": "R\u00e9glementation Environnementale 2020 \u2014 exigences \u00e9nerg\u00e9tiques et carbone pour les b\u00e2timents neufs.",
  MAPA: "March\u00e9 \u00c0 Proc\u00e9dure Adapt\u00e9e \u2014 proc\u00e9dure simplifi\u00e9e sous les seuils europ\u00e9ens.",
  "SLA 99.9%": "Service Level Agreement \u2014 engagement de disponibilit\u00e9 du service (99.9% = max 8h45 d'indisponibilit\u00e9/an).",
  RGE: "Reconnu Garant de l'Environnement \u2014 qualification pour les travaux de r\u00e9novation \u00e9nerg\u00e9tique.",
  OS: "Ordre de Service \u2014 notification officielle de d\u00e9marrage des travaux par le ma\u00eetre d'ouvrage.",
};

interface BtpTooltipProps {
  term: string;
  children?: React.ReactNode;
}

export default function BtpTooltip({ term, children }: BtpTooltipProps) {
  const [show, setShow] = useState(false);
  const ref = useRef<HTMLSpanElement>(null);
  const definition = BTP_TERMS[term];

  if (!definition) {
    return <>{children || term}</>;
  }

  return (
    <span
      ref={ref}
      className="relative inline-flex items-center cursor-help"
      onMouseEnter={() => setShow(true)}
      onMouseLeave={() => setShow(false)}
    >
      <span className="border-b border-dashed border-slate-400 dark:border-slate-500">
        {children || term}
      </span>
      {show && (
        <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 z-50 w-72 p-3 bg-slate-900 dark:bg-slate-700 text-white text-xs leading-relaxed rounded-xl shadow-lg pointer-events-none animate-fade-in">
          <span className="font-bold text-primary-300">{term}</span>
          <br />
          {definition}
          <span className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2 w-2 h-2 bg-slate-900 dark:bg-slate-700 rotate-45" />
        </span>
      )}
    </span>
  );
}

export { BTP_TERMS };
