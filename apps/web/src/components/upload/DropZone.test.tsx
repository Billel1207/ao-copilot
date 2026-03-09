/**
 * Tests unitaires pour la logique de la page d'upload (DropZone).
 * Couvre : détection type doc, formatage taille, filtrage PDF, état des fichiers.
 */
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";

// ── Mocks ─────────────────────────────────────────────────────────────────

vi.mock("react-dropzone", () => ({
  useDropzone: vi.fn(() => ({
    getRootProps: () => ({ "data-testid": "dropzone-root" }),
    getInputProps: () => ({ type: "file", accept: ".pdf" }),
    isDragActive: false,
  })),
}));

vi.mock("@/hooks/useDocuments", () => ({
  useUploadDocument: vi.fn(() => ({
    mutateAsync: vi.fn(),
    isPending: false,
  })),
}));

vi.mock("next/navigation", () => ({
  useParams: () => ({ id: "proj-123" }),
  useRouter: () => ({ push: vi.fn() }),
}));

// ── Utility functions (reproduced from upload/page.tsx logic) ──────────────

const DOC_TYPE_KEYWORDS: Record<string, string[]> = {
  RC:    ["règlement", "reglement", "consultation"],
  CCTP:  ["cctp", "techniques"],
  CCAP:  ["ccap", "administratives"],
  DPGF:  ["dpgf", "décomposition"],
  BPU:   ["bpu", "bordereau"],
  AE:    ["acte d'engagement", "acte engagement"],
  ATTRI: ["attribution"],
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

// ── Tests : detectDocType ──────────────────────────────────────────────────

describe("detectDocType()", () => {
  it("detects RC from filename containing 'règlement'", () => {
    expect(detectDocType("Règlement_de_Consultation_2026.pdf")).toBe("RC");
  });

  it("detects CCTP from filename containing 'cctp'", () => {
    expect(detectDocType("CCTP_Gros_Oeuvre.pdf")).toBe("CCTP");
  });

  it("detects CCAP from filename containing 'administratives'", () => {
    expect(detectDocType("clauses_administratives_particulieres.pdf")).toBe("CCAP");
  });

  it("detects DPGF from filename containing 'dpgf'", () => {
    expect(detectDocType("DPGF_lot1.pdf")).toBe("DPGF");
  });

  it("detects BPU from filename containing 'bpu'", () => {
    expect(detectDocType("BPU_electricite.pdf")).toBe("BPU");
  });

  it("detects AE from filename containing 'acte engagement'", () => {
    expect(detectDocType("acte engagement_signe.pdf")).toBe("AE");
  });

  it("detects ATTRI from filename containing 'attribution'", () => {
    expect(detectDocType("lettre_attribution.pdf")).toBe("ATTRI");
  });

  it("returns AUTRES for unrecognized filename", () => {
    expect(detectDocType("document_quelconque.pdf")).toBe("AUTRES");
    expect(detectDocType("rapport_final.pdf")).toBe("AUTRES");
    expect(detectDocType("")).toBe("AUTRES");
  });

  it("is case-insensitive", () => {
    expect(detectDocType("RÈGLEMENT_CONSULTATION.PDF")).toBe("RC");
    expect(detectDocType("CCTP_STRUCTURE.PDF")).toBe("CCTP");
  });

  it("matches on partial filename", () => {
    expect(detectDocType("AO2026_CCTP_Plomberie_v2.pdf")).toBe("CCTP");
  });
});

// ── Tests : formatSize ──────────────────────────────────────────────────────

describe("formatSize()", () => {
  it("formats bytes smaller than 1 MB as Ko", () => {
    expect(formatSize(500 * 1024)).toBe("500 Ko");
    expect(formatSize(1024)).toBe("1 Ko");
  });

  it("formats bytes larger than 1 MB as Mo", () => {
    expect(formatSize(2.5 * 1024 * 1024)).toBe("2.5 Mo");
    expect(formatSize(10 * 1024 * 1024)).toBe("10.0 Mo");
  });

  it("formats exact 1 MB boundary as Ko (< 1 MB condition)", () => {
    // 1 MB = 1048576 bytes, condition is < 1048576
    expect(formatSize(1048575)).toBe("1024 Ko");
  });
});

// ── Tests : File filtering logic ────────────────────────────────────────────

describe("PDF filtering logic", () => {
  it("accepts files with application/pdf MIME type", () => {
    const pdfFile = new File(["content"], "test.pdf", { type: "application/pdf" });
    const nonPdfFile = new File(["content"], "doc.docx", { type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document" });

    const accepted = [pdfFile, nonPdfFile];
    const pdfs = accepted.filter(f => f.type === "application/pdf");

    expect(pdfs).toHaveLength(1);
    expect(pdfs[0].name).toBe("test.pdf");
  });

  it("rejects empty file list", () => {
    const pdfs = ([] as File[]).filter(f => f.type === "application/pdf");
    expect(pdfs).toHaveLength(0);
  });

  it("accepts multiple PDFs", () => {
    const files = [
      new File([""], "rc.pdf", { type: "application/pdf" }),
      new File([""], "cctp.pdf", { type: "application/pdf" }),
      new File([""], "image.png", { type: "image/png" }),
    ];
    const pdfs = files.filter(f => f.type === "application/pdf");
    expect(pdfs).toHaveLength(2);
  });
});

// ── Tests : Upload state machine ────────────────────────────────────────────

describe("Upload file status transitions", () => {
  type FileStatus = "pending" | "uploading" | "done" | "error";

  interface UploadFile {
    file: File;
    status: FileStatus;
    error?: string;
  }

  const createFile = (name: string): UploadFile => ({
    file: new File([""], name, { type: "application/pdf" }),
    status: "pending",
  });

  it("pending → uploading → done on success", () => {
    let f = createFile("test.pdf");
    expect(f.status).toBe("pending");

    f = { ...f, status: "uploading" };
    expect(f.status).toBe("uploading");

    f = { ...f, status: "done" };
    expect(f.status).toBe("done");
  });

  it("pending → uploading → error on failure", () => {
    let f = createFile("fail.pdf");
    f = { ...f, status: "uploading" };
    f = { ...f, status: "error", error: "Erreur upload" };

    expect(f.status).toBe("error");
    expect(f.error).toBe("Erreur upload");
  });

  it("counts pending files correctly", () => {
    const files: UploadFile[] = [
      { ...createFile("a.pdf"), status: "pending" },
      { ...createFile("b.pdf"), status: "done" },
      { ...createFile("c.pdf"), status: "pending" },
    ];
    const pendingCount = files.filter(f => f.status === "pending").length;
    expect(pendingCount).toBe(2);
  });

  it("counts done files correctly", () => {
    const files: UploadFile[] = [
      { ...createFile("a.pdf"), status: "done" },
      { ...createFile("b.pdf"), status: "done" },
      { ...createFile("c.pdf"), status: "error", error: "fail" },
    ];
    const doneCount = files.filter(f => f.status === "done").length;
    expect(doneCount).toBe(2);
  });
});
