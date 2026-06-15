import clsx from "clsx";
import { ClaimStatus } from "../types";

const STATUS_STYLES: Record<ClaimStatus, string> = {
  draft:        "bg-slate-100 text-slate-600 border-slate-200",
  processing:   "bg-blue-50 text-blue-600 border-blue-200",
  extracted:    "bg-violet-50 text-violet-600 border-violet-200",
  under_review: "bg-amber-50 text-amber-700 border-amber-200",
  ready:        "bg-teal-50 text-teal-700 border-teal-200",
  submitted:    "bg-indigo-50 text-indigo-700 border-indigo-200",
  paid:         "bg-emerald-50 text-emerald-700 border-emerald-200",
  rejected:     "bg-red-50 text-red-600 border-red-200",
};

const STATUS_LABELS: Record<ClaimStatus, string> = {
  draft:        "Draft",
  processing:   "Processing…",
  extracted:    "Extracted",
  under_review: "Under Review",
  ready:        "Ready",
  submitted:    "Submitted",
  paid:         "Paid",
  rejected:     "Rejected",
};

export default function ClaimStatusBadge({ status }: { status: ClaimStatus }) {
  return (
    <span
      className={clsx(
        "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border",
        STATUS_STYLES[status]
      )}
    >
      {status === "processing" && (
        <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse mr-1.5" />
      )}
      {STATUS_LABELS[status]}
    </span>
  );
}
