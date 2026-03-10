"use client";

import { ScanSearch, CheckCircle, AlertTriangle, XCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface OcrQualityBannerProps {
  /** OCR quality score between 0 and 100 */
  quality: number | null | undefined;
  /** Additional CSS classes */
  className?: string;
  /** Document name for context */
  documentName?: string;
}

/**
 * Banner indicating the OCR quality of a document.
 *
 * - quality < 50  → red "Document source très dégradé"
 * - quality < 70  → orange "Document source de mauvaise qualité"
 * - quality < 85  → amber "Qualité OCR moyenne"
 * - quality ≥ 85  → hidden (unless always shown)
 * - quality null   → hidden
 */
export default function OcrQualityBanner({
  quality,
  className,
  documentName,
}: OcrQualityBannerProps) {
  if (quality == null || quality === undefined) return null;

  // Good quality — don't show
  if (quality >= 85) return null;

  const docLabel = documentName ? ` (${documentName})` : "";

  // Very poor quality
  if (quality < 50) {
    return (
      <div
        className={cn(
          "flex items-start gap-2.5 bg-red-50 border border-red-200 rounded-xl px-4 py-2.5",
          className
        )}
      >
        <XCircle className="w-4 h-4 text-red-600 flex-shrink-0 mt-0.5" />
        <div>
          <p className="text-xs font-semibold text-red-800">
            Document source très dégradé{docLabel} — Qualité OCR : {quality}%
          </p>
          <p className="text-[11px] text-red-700 mt-0.5">
            Le texte extrait contient probablement de nombreuses erreurs. Les résultats d&apos;analyse
            peuvent être significativement impactés. Privilégiez un scan de meilleure qualité.
          </p>
        </div>
      </div>
    );
  }

  // Poor quality
  if (quality < 70) {
    return (
      <div
        className={cn(
          "flex items-start gap-2.5 bg-orange-50 border border-orange-200 rounded-xl px-4 py-2.5",
          className
        )}
      >
        <AlertTriangle className="w-4 h-4 text-orange-600 flex-shrink-0 mt-0.5" />
        <div>
          <p className="text-xs font-semibold text-orange-800">
            Document source de mauvaise qualité{docLabel} — Qualité OCR : {quality}%
          </p>
          <p className="text-[11px] text-orange-700 mt-0.5">
            Certaines parties du texte ont pu être mal interprétées. Vérifiez les données critiques
            (montants, dates, noms) directement dans le document original.
          </p>
        </div>
      </div>
    );
  }

  // Average quality
  return (
    <div
      className={cn(
        "flex items-center gap-2.5 bg-amber-50 border border-amber-200 rounded-xl px-4 py-2.5",
        className
      )}
    >
      <ScanSearch className="w-4 h-4 text-amber-600 flex-shrink-0" />
      <p className="text-xs text-amber-800">
        <span className="font-semibold">Qualité OCR moyenne{docLabel} : {quality}%</span>
        {" — "}Certaines données pourraient nécessiter une vérification.
      </p>
    </div>
  );
}
