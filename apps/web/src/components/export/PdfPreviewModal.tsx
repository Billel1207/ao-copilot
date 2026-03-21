"use client";

import { useState } from "react";
import { X, Download, Maximize2, Minimize2, Loader2 } from "lucide-react";

interface PdfPreviewModalProps {
  url: string;
  filename?: string;
  onClose: () => void;
}

/**
 * Modal de preview PDF inline.
 *
 * Affiche le PDF dans un <iframe> avant téléchargement.
 * Boutons : Télécharger, Plein écran, Fermer.
 */
export function PdfPreviewModal({ url, filename = "export.pdf", onClose }: PdfPreviewModalProps) {
  const [fullscreen, setFullscreen] = useState(false);
  const [loading, setLoading] = useState(true);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden
      />

      {/* Modal */}
      <div
        className={`relative bg-white rounded-2xl shadow-2xl flex flex-col transition-all duration-300 ${
          fullscreen
            ? "w-[98vw] h-[98vh]"
            : "w-[90vw] max-w-5xl h-[85vh]"
        }`}
        role="dialog"
        aria-label="Aperçu PDF"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-red-50 flex items-center justify-center">
              <svg className="w-4 h-4 text-red-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
                <line x1="16" y1="13" x2="8" y2="13" />
                <line x1="16" y1="17" x2="8" y2="17" />
              </svg>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-slate-800">{filename}</h3>
              <p className="text-[10px] text-slate-400">Aperçu avant téléchargement</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <a
              href={url}
              download={filename}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-white
                         bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors"
            >
              <Download className="w-3.5 h-3.5" />
              Télécharger
            </a>
            <button
              onClick={() => setFullscreen(!fullscreen)}
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
              title={fullscreen ? "Réduire" : "Plein écran"}
            >
              {fullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-red-500 hover:bg-red-50 transition-colors"
              title="Fermer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* PDF iframe */}
        <div className="flex-1 relative bg-slate-100 rounded-b-2xl overflow-hidden">
          {loading && (
            <div className="absolute inset-0 flex items-center justify-center bg-white/80 z-10">
              <div className="flex flex-col items-center gap-2">
                <Loader2 className="w-6 h-6 text-primary-500 animate-spin" />
                <p className="text-xs text-slate-400">Chargement du PDF...</p>
              </div>
            </div>
          )}
          <iframe
            src={`${url}#toolbar=1&navpanes=0`}
            className="w-full h-full border-0"
            title="Aperçu PDF"
            onLoad={() => setLoading(false)}
          />
        </div>
      </div>
    </div>
  );
}
