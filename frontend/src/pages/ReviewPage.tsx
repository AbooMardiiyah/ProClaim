/**
 * ProClaim — Review Screen
 * Left: PDF viewer | Right: extracted fields with confidence indicators + inline edit
 */
import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import {
  Download,
  Loader2,
  AlertCircle,
  FileSearch,
  FileSpreadsheet,
  FileJson,
  X,
} from "lucide-react";
import toast from "react-hot-toast";
import { useClaim, useTransitionStatus, useUpdateField } from "../hooks/useClaims";
import { useMe } from "../hooks/useAuth";
import FieldEditor from "../components/FieldEditor";
import ClaimStatusBadge from "../components/ClaimStatusBadge";
import api from "../lib/api";
import { ClaimField } from "../types";

export default function ReviewPage() {
  const { id } = useParams<{ id: string }>();
  const { data: claim, isLoading, isError } = useClaim(id);
  const { data: me } = useMe();
  const isAdmin = me?.role === "admin";
  const updateField = useUpdateField(id!);
  const transitionStatus = useTransitionStatus(id!);

  const [selectedDocIndex, setSelectedDocIndex] = useState(0);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [citedField, setCitedField] = useState<ClaimField | null>(null);

  // ── ALL HOOKS MUST BE BEFORE ANY EARLY RETURN ──
  const activeDoc = claim?.documents?.[selectedDocIndex];

  useEffect(() => {
    if (!activeDoc) {
      setPdfUrl(null);
      return;
    }
    let objectUrl: string | null = null;
    const fetchPdf = async () => {
      setPdfLoading(true);
      try {
        const response = await api.get(
          `/claims/${claim!.id}/documents/${activeDoc.id}/download`,
          { responseType: "blob" }
        );
        objectUrl = URL.createObjectURL(response.data);
        setPdfUrl(objectUrl);
      } catch {
        toast.error("Failed to load PDF preview");
        setPdfUrl(null);
      } finally {
        setPdfLoading(false);
      }
    };
    fetchPdf();
    return () => {
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [activeDoc?.id, claim?.id]);

  // ── EARLY RETURNS AFTER ALL HOOKS ──
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 text-teal-500 animate-spin" />
      </div>
    );
  }

  if (isError || !claim) {
    return (
      <div className="flex items-center justify-center h-full flex-col gap-4">
        <AlertCircle className="w-10 h-10 text-red-400" />
        <p className="text-slate-600">Claim not found.</p>
        <Link to="/claims" className="text-teal-600 hover:underline text-sm">
          ← Back to claims
        </Link>
      </div>
    );
  }

  const handleCite = (field: ClaimField) => {
    setCitedField(field);
    if (field.source_document_id && claim) {
      const docIdx = claim.documents.findIndex((d) => d.id === field.source_document_id);
      if (docIdx !== -1) setSelectedDocIndex(docIdx);
    }
  };

  const handleFieldSave = async (fieldKey: string, value: string, note?: string) => {
    try {
      await updateField.mutateAsync({ fieldKey, value, note });
      toast.success("Field saved");
    } catch {
      toast.error("Failed to save field");
    }
  };

  const handleMarkUnderReview = async () => {
    try {
      await transitionStatus.mutateAsync({ status: "under_review", note: "Started review" });
      toast.success("Claim moved to Under Review");
    } catch (e: any) {
      toast.error(e?.response?.data?.detail ?? "Transition failed");
    }
  };

  const handleMarkReady = async () => {
    try {
      await transitionStatus.mutateAsync({ status: "ready", note: "Review complete" });
      toast.success("Claim marked as Ready");
    } catch (e: any) {
      toast.error(e?.response?.data?.detail ?? "Transition failed");
    }
  };

  const handleExport = async (format: "csv" | "excel") => {
    try {
      const response = await api.get(
        `/claims/${claim.id}/export?format=${format}`,
        { responseType: "blob" }
      );
      const mimeType =
        format === "csv"
          ? "text/csv"
          : "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";
      const extension = format === "csv" ? "csv" : "xlsx";
      const blob = new Blob([response.data], { type: mimeType });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${claim.reference_number}.${extension}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      toast.error("Export failed");
    }
  };

  const missingCount = claim.fields.filter((f) => f.status === "missing").length;
  const isProcessing = claim.status === "processing";

  return (
    <div className="flex h-full overflow-hidden">
      {/* ── LEFT: PDF Viewer ───────────────────────────────────────────── */}
      <div className="w-[45%] bg-slate-800 flex flex-col border-r border-slate-700">
        {/* Doc tabs */}
        <div className="flex items-center gap-1 px-3 pt-3 pb-0 flex-wrap">
          {claim.documents.map((doc, i) => (
            <button
              key={doc.id}
              onClick={() => setSelectedDocIndex(i)}
              className={`text-xs px-3 py-1.5 rounded-t-md font-medium transition-colors ${
                i === selectedDocIndex
                  ? "bg-white text-slate-800"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              {doc.file_name.length > 20
                ? doc.file_name.slice(0, 18) + "…"
                : doc.file_name}
            </button>
          ))}
          {!claim.documents.length && (
            <span className="text-xs text-slate-400 px-3 py-1.5">No documents</span>
          )}
        </div>

        {/* Citation banner */}
        {citedField && citedField.source_document_id && (
          <div className="mx-3 mt-2 bg-teal-900/60 border border-teal-600/50 rounded-lg px-3 py-2 flex items-start gap-2">
            <FileSearch className="w-3.5 h-3.5 text-teal-400 mt-0.5 shrink-0" />
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-teal-300">
                Source for: <span className="text-white">{citedField.field_label}</span>
              </p>
              <p className="text-xs text-teal-400 mt-0.5 truncate">
                "{citedField.value}"
              </p>
              {citedField.page_number !== null && (
                <p className="text-xs text-teal-500 mt-0.5">Page {citedField.page_number + 1}</p>
              )}
            </div>
            <button onClick={() => setCitedField(null)} className="text-teal-500 hover:text-white shrink-0">
              <X className="w-3 h-3" />
            </button>
          </div>
        )}

        {/* PDF canvas */}
        <div className="flex-1 overflow-hidden relative">
          {pdfLoading ? (
            <div className="flex items-center justify-center h-full">
              <Loader2 className="w-6 h-6 text-slate-400 animate-spin" />
            </div>
          ) : pdfUrl ? (
            <iframe
              src={pdfUrl}
              title="PDF Preview"
              className="w-full h-full border-0"
            />
          ) : (
            <div className="flex items-center justify-center h-full text-slate-500 text-sm">
              No document to preview
            </div>
          )}
        </div>
      </div>

      {/* ── RIGHT: Fields Panel ────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col overflow-hidden bg-slate-50">
        {/* Header */}
        <div className="px-6 py-4 bg-white border-b border-slate-200">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-3 mb-1">
                <Link
                  to="/claims"
                  className="text-slate-400 hover:text-slate-600 text-sm"
                >
                  ← Claims
                </Link>
                <span className="font-mono text-sm text-slate-400">/</span>
                <span className="font-mono text-sm text-slate-600">
                  {claim.reference_number}
                </span>
              </div>
              <div className="flex items-center gap-3">
                <h1 className="text-lg font-bold text-slate-800">
                  {claim.patient_name ?? "Unnamed Patient"}
                </h1>
                <ClaimStatusBadge status={claim.status} />
              </div>
              {missingCount > 0 && (
                <p className="text-xs text-red-500 mt-1">
                  ⚠ {missingCount} field{missingCount > 1 ? "s" : ""} missing — review required
                </p>
              )}
            </div>

            {/* Action buttons */}
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1.5">
                <button
                  onClick={() => handleExport("csv")}
                  className="flex items-center gap-1.5 text-sm text-slate-600 hover:text-slate-800 border border-slate-300 px-3 py-1.5 rounded-lg transition-colors"
                >
                  <Download className="w-3.5 h-3.5" />
                  CSV
                </button>
                <button
                  onClick={() => handleExport("excel")}
                  className="flex items-center gap-1.5 text-sm text-slate-600 hover:text-slate-800 border border-slate-300 px-3 py-1.5 rounded-lg transition-colors"
                  title="Download Excel"
                >
                  <FileSpreadsheet className="w-3.5 h-3.5" />
                  Excel
                </button>
              </div>

              {claim.status === "extracted" ? (
                <button
                  onClick={handleMarkUnderReview}
                  disabled={transitionStatus.isPending}
                  className="flex items-center gap-1.5 text-sm bg-amber-600 hover:bg-amber-700 text-white px-4 py-1.5 rounded-lg transition-colors disabled:opacity-50"
                >
                  Mark Under Review
                </button>
              ) : null}

              {claim.status === "under_review" && isAdmin ? (
                <button
                  onClick={handleMarkReady}
                  disabled={transitionStatus.isPending}
                  className="flex items-center gap-1.5 text-sm bg-[#028090] hover:bg-[#026070] text-white px-4 py-1.5 rounded-lg transition-colors disabled:opacity-50"
                >
                  Mark Ready
                </button>
              ) : null}

              {claim.status === "ready" ? (
                <button
                  disabled
                  title="HMO submission is coming soon"
                  className="flex items-center gap-1.5 text-sm bg-slate-400 text-white px-4 py-1.5 rounded-lg cursor-not-allowed opacity-60"
                >
                  <FileJson className="w-3.5 h-3.5" />
                  Submit to HMO (Coming Soon)
                </button>
              ) : null}
            </div>
          </div>
        </div>

        {/* Processing overlay */}
        {isProcessing && (
          <div className="mx-6 mt-4 bg-blue-50 border border-blue-200 rounded-xl p-4 flex items-center gap-3">
            <Loader2 className="w-5 h-5 text-blue-500 animate-spin shrink-0" />
            <div>
              <p className="text-sm font-semibold text-blue-700">
                AI is processing your documents…
              </p>
              <p className="text-xs text-blue-500 mt-0.5">
                This page will update automatically when extraction is complete.
              </p>
            </div>
          </div>
        )}

        {/* Fields table */}
        <div className="flex-1 overflow-auto px-6 py-4">
          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-slate-400 uppercase tracking-wide border-b border-slate-100 bg-slate-50">
                  <th className="px-4 py-3 font-medium">Field</th>
                  <th className="px-4 py-3 font-medium">Value</th>
                  <th className="px-4 py-3 font-medium">Confidence</th>
                  <th className="px-4 py-3 font-medium w-24"></th>
                </tr>
              </thead>
              <tbody>
                {claim.fields.length > 0 ? (
                  claim.fields.map((field) => (
                    <FieldEditor
                      key={field.id}
                      field={field}
                      onSave={handleFieldSave}
                      onCite={handleCite}
                      isCited={citedField?.id === field.id}
                      saving={updateField.isPending}
                    />
                  ))
                ) : (
                  <tr>
                    <td colSpan={4} className="px-4 py-10 text-center text-slate-400 text-sm">
                      {isProcessing
                        ? "Waiting for extraction results…"
                        : "No fields extracted yet. Trigger extraction to populate this table."}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Confidence legend */}
          <div className="flex items-center gap-4 mt-4 text-xs text-slate-500">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500" /> &gt;90% High confidence
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-amber-400" /> 70–90% Review recommended
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-red-500" /> &lt;70% or Missing
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
