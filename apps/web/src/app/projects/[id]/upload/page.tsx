"use client";
import { useCallback, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useDropzone } from "react-dropzone";
import {
  Upload, FileText, X, CheckCircle2, Loader2, ArrowLeft,
  AlertCircle, CloudUpload, Image as ImageIcon, FileType2,
} from "lucide-react";
import { toast } from "sonner";
import Link from "next/link";
import { useUploadDocument } from "@/hooks/useDocuments";
import { cn } from "@/lib/utils";

// ── Types ──────────────────────────────────────────────────────────────
interface UploadFile {
  file: File;
  status: "pending" | "uploading" | "done" | "error";
  error?: string;
  docType?: string;
}

// ── Document type detection from filename ─────────────────────────────
const DOC_TYPE_KEYWORDS: Record<string, string[]> = {
  RC:    ["règlement", "reglement", "consultation"],
  CCTP:  ["cctp", "techniques"],
  CCAP:  ["ccap", "administratives"],
  DPGF:  ["dpgf", "décomposition"],
  BPU:   ["bpu", "bordereau"],
  AE:    ["acte d'engagement", "acte engagement"],
  ATTRI: ["attribution"],
};

const DOC_TYPE_COLORS: Record<string, string> = {
  RC:     "bg-primary-100 text-primary-800",
  CCTP:   "bg-blue-100 text-blue-800",
  CCAP:   "bg-success-100 text-success-700",
  DPGF:   "bg-warning-100 text-warning-700",
  BPU:    "bg-purple-100 text-purple-700",
  AE:     "bg-pink-100 text-pink-700",
  ATTRI:  "bg-indigo-100 text-indigo-700",
  AUTRES: "bg-slate-100 text-slate-600",
};

function detectDocType(filename: string): string {
  const lower = filename.toLowerCase();
  for (const [type, keywords] of Object.entries(DOC_TYPE_KEYWORDS)) {
    if (keywords.some(k => lower.includes(k))) return type;
  }
  return "AUTRES";
}

function formatSize(bytes: number): string {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} Ko`;
  return `${(bytes / 1024 / 1024).toFixed(1)} Mo`;
}

// ── File Row ───────────────────────────────────────────────────────────
function fileIcon(file: File) {
  if (file.type.startsWith("image/")) return <ImageIcon className="w-4 h-4 text-blue-400" />;
  if (file.name.endsWith(".docx"))   return <FileType2 className="w-4 h-4 text-indigo-400" />;
  return <FileText className="w-4 h-4 text-slate-400" />;
}

function FileRow({
  f,
  index,
  onRemove,
}: {
  f: UploadFile;
  index: number;
  onRemove: (i: number) => void;
}) {
  const docTypeColor = DOC_TYPE_COLORS[f.docType ?? "AUTRES"];

  return (
    <div className={`card p-3.5 flex items-center gap-3 animate-slide-up
      ${f.status === "done" ? "border-l-4 border-l-success-500" :
        f.status === "error" ? "border-l-4 border-l-danger-500" :
        f.status === "uploading" ? "border-l-4 border-l-primary-500" :
        "border-l-4 border-l-slate-200"}`}>
      {/* Icône */}
      <div className="w-8 h-8 bg-slate-50 rounded-lg flex items-center justify-center flex-shrink-0">
        {fileIcon(f.file)}
      </div>

      {/* Infos */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <p className="text-sm font-medium text-slate-800 truncate max-w-xs">{f.file.name}</p>
          {f.docType && (
            <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${docTypeColor}`}>
              {f.docType}
            </span>
          )}
        </div>
        <p className="text-xs text-slate-400 mt-0.5">{formatSize(f.file.size)}</p>

        {/* Progress bar during upload */}
        {f.status === "uploading" && (
          <div className="mt-1.5 h-1 bg-slate-100 rounded-full overflow-hidden">
            <div className="h-full bg-primary-600 rounded-full animate-pulse-soft w-3/4" />
          </div>
        )}
      </div>

      {/* Status indicator */}
      <div className="flex-shrink-0">
        {f.status === "pending" && (
          <button
            onClick={() => onRemove(index)}
            className="text-slate-300 hover:text-danger-400 transition-colors p-1 rounded-lg hover:bg-danger-50"
            title="Retirer"
          >
            <X className="w-4 h-4" />
          </button>
        )}
        {f.status === "uploading" && (
          <Loader2 className="w-4 h-4 animate-spin text-primary-600" />
        )}
        {f.status === "done" && (
          <CheckCircle2 className="w-4 h-4 text-success-600" />
        )}
        {f.status === "error" && (
          <div className="flex items-center gap-1 text-danger-600">
            <AlertCircle className="w-4 h-4" />
            <span className="text-xs">{f.error}</span>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Main Page ──────────────────────────────────────────────────────────
export default function UploadPage() {
  const params = useParams();
  const projectId = params.id as string;
  const router = useRouter();
  const [files, setFiles] = useState<UploadFile[]>([]);
  const [uploading, setUploading] = useState(false);
  const upload = useUploadDocument(projectId);

  const onDrop = useCallback((accepted: File[]) => {
    const newFiles: UploadFile[] = accepted.map(file => ({
      file,
      status: "pending",
      docType: detectDocType(file.name),
    }));
    setFiles(prev => [...prev, ...newFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "image/jpeg": [".jpg", ".jpeg"],
      "image/png": [".png"],
      "image/tiff": [".tiff", ".tif"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
    },
    maxSize: 52_428_800,
  });

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleUploadAll = async () => {
    const pending = files.filter(f => f.status === "pending");
    if (pending.length === 0) return;
    setUploading(true);

    for (let i = 0; i < files.length; i++) {
      if (files[i].status !== "pending") continue;
      setFiles(prev => {
        const n = [...prev];
        n[i] = { ...n[i], status: "uploading" };
        return n;
      });
      try {
        await upload.mutateAsync(files[i].file);
        setFiles(prev => {
          const n = [...prev];
          n[i] = { ...n[i], status: "done" };
          return n;
        });
      } catch {
        setFiles(prev => {
          const n = [...prev];
          n[i] = { ...n[i], status: "error", error: "Erreur upload" };
          return n;
        });
      }
    }
    setUploading(false);
    const doneCount = files.filter(f => f.status === "done").length;
    toast.success(`${doneCount} fichier${doneCount > 1 ? "s" : ""} importé${doneCount > 1 ? "s" : ""} avec succès`);
    setTimeout(() => router.push(`/projects/${projectId}`), 1200);
  };

  const pendingCount = files.filter(f => f.status === "pending").length;
  const doneCount = files.filter(f => f.status === "done").length;

  return (
    <div className="p-6 md:p-8 max-w-2xl mx-auto">
      {/* Breadcrumb */}
      <Link
        href={`/projects/${projectId}`}
        className="inline-flex items-center gap-1.5 text-slate-400 text-xs hover:text-primary-700 transition-colors mb-6"
      >
        <ArrowLeft className="w-3 h-3" /> Retour au projet
      </Link>

      <div className="mb-6">
        <h1 className="text-xl font-bold text-slate-900">Importer des documents DCE</h1>
        <p className="text-slate-500 text-sm mt-1">
          RC, CCTP, CCAP, DPGF, BPU, AE… — PDF, Word (.docx), images (JPEG, PNG, TIFF) — 50 Mo max.
        </p>
      </div>

      {/* ── Dropzone animée ── */}
      <div
        {...getRootProps()}
        className={cn(
          "relative border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer",
          "transition-all duration-200 group mb-5",
          isDragActive
            ? "border-primary-500 bg-primary-50 scale-[1.01] shadow-elevation"
            : "border-slate-200 hover:border-primary-300 hover:bg-primary-50/30"
        )}
      >
        <input {...getInputProps()} />

        {/* Cloud icon animé */}
        <div className={cn(
          "w-16 h-16 rounded-2xl mx-auto mb-4 flex items-center justify-center transition-all duration-200",
          isDragActive
            ? "bg-primary-100 text-primary-600 scale-110"
            : "bg-slate-100 text-slate-400 group-hover:bg-primary-50 group-hover:text-primary-500"
        )}>
          <CloudUpload className="w-8 h-8" />
        </div>

        <p className={cn(
          "text-sm font-semibold transition-colors duration-200",
          isDragActive ? "text-primary-700" : "text-slate-700"
        )}>
          {isDragActive
            ? "✨ Relâchez pour importer"
            : "Glissez vos fichiers ici, ou cliquez pour sélectionner"}
        </p>
        <p className="text-xs text-slate-400 mt-1">
          PDF · Word (.docx) · Images (JPEG, PNG, TIFF) — max 50 Mo
        </p>

        {/* Hint types de documents */}
        {!isDragActive && (
          <div className="flex flex-wrap items-center justify-center gap-1.5 mt-4">
            {["RC", "CCTP", "CCAP", "DPGF", "BPU", "AE"].map(t => (
              <span key={t} className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${DOC_TYPE_COLORS[t]}`}>
                {t}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* ── Liste de fichiers ── */}
      {files.length > 0 && (
        <div className="space-y-2 mb-6">
          {files.map((f, i) => (
            <FileRow key={i} f={f} index={i} onRemove={removeFile} />
          ))}
        </div>
      )}

      {/* ── Actions ── */}
      {pendingCount > 0 && (
        <button
          onClick={handleUploadAll}
          disabled={uploading}
          className="btn-primary-gradient flex items-center gap-2"
        >
          {uploading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Import en cours...
            </>
          ) : (
            <>
              <Upload className="w-4 h-4" />
              Importer {pendingCount} fichier{pendingCount > 1 ? "s" : ""}
            </>
          )}
        </button>
      )}

      {doneCount > 0 && pendingCount === 0 && !uploading && (
        <div className="flex items-center gap-2 text-success-700 text-sm font-medium bg-success-50 rounded-xl px-4 py-3">
          <CheckCircle2 className="w-4 h-4" />
          {doneCount} fichier{doneCount > 1 ? "s" : ""} importé{doneCount > 1 ? "s" : ""} — redirection en cours...
        </div>
      )}
    </div>
  );
}
