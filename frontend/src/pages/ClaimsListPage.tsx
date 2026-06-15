import { useState } from "react";
import { Link } from "react-router-dom";
import { Search, Plus, Trash2 } from "lucide-react";
import { format } from "date-fns";
import toast from "react-hot-toast";
import { useClaims, useDeleteClaim } from "../hooks/useClaims";
import { useMe } from "../hooks/useAuth";
import ClaimStatusBadge from "../components/ClaimStatusBadge";
import { ClaimStatus } from "../types";

const STATUS_OPTIONS: { label: string; value: ClaimStatus | "" }[] = [
  { label: "All statuses", value: "" },
  { label: "Draft", value: "draft" },
  { label: "Processing", value: "processing" },
  { label: "Under Review", value: "under_review" },
  { label: "Ready", value: "ready" },
  { label: "Submitted", value: "submitted" },
  { label: "Paid", value: "paid" },
  { label: "Rejected", value: "rejected" },
];

export default function ClaimsListPage() {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<ClaimStatus | "">("");
  const [page, setPage] = useState(1);

  const { data: me } = useMe();
  const isAdmin = me?.role === "admin";
  const deleteClaim = useDeleteClaim();

  const handleDelete = (claimId: string, ref: string) => {
    if (!confirm(`Permanently delete claim ${ref}? This cannot be undone.`)) return;
    deleteClaim.mutate(claimId, {
      onSuccess: () => toast.success("Claim deleted"),
      onError: () => toast.error("Failed to delete claim"),
    });
  };

  const { data, isLoading } = useClaims({
    page,
    page_size: 15,
    status: status || undefined,
    search: search || undefined,
  });

  return (
    <div className="p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Claims</h1>
          <p className="text-slate-500 text-sm mt-0.5">
            {data?.total ?? 0} total claims
          </p>
        </div>
        <Link
          to="/upload"
          className="flex items-center gap-2 bg-[#028090] hover:bg-[#026070] text-white text-sm font-semibold px-4 py-2.5 rounded-xl transition-colors"
        >
          <Plus className="w-4 h-4" />
          New Claim
        </Link>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 mb-5">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            placeholder="Search patient name or NHIA ID…"
            className="w-full border border-slate-300 rounded-lg pl-9 pr-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/40 focus:border-teal-500"
          />
        </div>

        <select
          value={status}
          onChange={(e) => { setStatus(e.target.value as ClaimStatus | ""); setPage(1); }}
          className="border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-teal-500/40 focus:border-teal-500 bg-white"
        >
          {STATUS_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-slate-400 uppercase tracking-wide border-b border-slate-100 bg-slate-50">
                <th className="px-5 py-3 font-medium">Reference</th>
                <th className="px-5 py-3 font-medium">Patient</th>
                <th className="px-5 py-3 font-medium">NHIA ID</th>
                <th className="px-5 py-3 font-medium">Date of Service</th>
                <th className="px-5 py-3 font-medium">Total Cost</th>
                <th className="px-5 py-3 font-medium">Docs</th>
                <th className="px-5 py-3 font-medium">Status</th>
                <th className="px-5 py-3 font-medium">Created</th>
                <th className="px-5 py-3 font-medium"></th>
              </tr>
            </thead>
            <tbody>
              {isLoading
                ? Array.from({ length: 8 }).map((_, i) => (
                    <tr key={i} className="border-b border-slate-50 animate-pulse">
                      {Array.from({ length: 9 }).map((_, j) => (
                        <td key={j} className="px-5 py-3">
                          <div className="h-3 bg-slate-100 rounded w-3/4" />
                        </td>
                      ))}
                    </tr>
                  ))
                : data?.items.map((claim) => (
                    <tr
                      key={claim.id}
                      className="border-b border-slate-50 hover:bg-slate-50/60 transition-colors"
                    >
                      <td className="px-5 py-3 font-mono text-xs text-slate-500">
                        {claim.reference_number}
                      </td>
                      <td className="px-5 py-3 font-medium text-slate-800">
                        {claim.patient_name ?? <span className="text-slate-400">—</span>}
                      </td>
                      <td className="px-5 py-3 text-slate-500">{claim.nhia_id ?? "—"}</td>
                      <td className="px-5 py-3 text-slate-500">{claim.date_of_service ?? "—"}</td>
                      <td className="px-5 py-3 text-slate-700">
                        {claim.total_cost
                          ? `₦${Number(claim.total_cost).toLocaleString()}`
                          : "—"}
                      </td>
                      <td className="px-5 py-3 text-slate-500 text-center">
                        {claim.document_count}
                      </td>
                      <td className="px-5 py-3">
                        <ClaimStatusBadge status={claim.status} />
                      </td>
                      <td className="px-5 py-3 text-slate-400 text-xs">
                        {format(new Date(claim.created_at), "d MMM yy")}
                      </td>
                      <td className="px-5 py-3">
                        <div className="flex items-center gap-3">
                          <Link
                            to={`/claims/${claim.id}`}
                            className="text-teal-600 hover:text-teal-700 font-medium whitespace-nowrap"
                          >
                            Review →
                          </Link>
                          {isAdmin && (
                            <button
                              onClick={() => handleDelete(claim.id, claim.reference_number)}
                              disabled={deleteClaim.isPending}
                              className="text-slate-300 hover:text-red-500 transition-colors disabled:opacity-40"
                              title="Delete claim"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
              {!isLoading && !data?.items.length && (
                <tr>
                  <td colSpan={9} className="px-5 py-12 text-center text-slate-400 text-sm">
                    No claims match your filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {data && data.total_pages > 1 && (
          <div className="flex items-center justify-between px-5 py-3 border-t border-slate-100 text-sm">
            <span className="text-slate-400 text-xs">
              {data.total} claims · page {data.page} of {data.total_pages}
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1 border border-slate-200 rounded-md disabled:opacity-40 hover:bg-slate-50 transition-colors"
              >
                Prev
              </button>
              <button
                onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))}
                disabled={page === data.total_pages}
                className="px-3 py-1 border border-slate-200 rounded-md disabled:opacity-40 hover:bg-slate-50 transition-colors"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
