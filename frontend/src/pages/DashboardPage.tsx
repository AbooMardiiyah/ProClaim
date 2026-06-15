import { useState } from "react";
import {
  Activity,
  CheckCircle2,
  Clock,
  FileText,
  AlertTriangle,
  ChevronRight,
} from "lucide-react";
import { Link } from "react-router-dom";
import { format } from "date-fns";
import KPICard from "../components/KPICard";
import ClaimStatusBadge from "../components/ClaimStatusBadge";
import { useClaims, useDashboardStats } from "../hooks/useClaims";
import { useMe } from "../hooks/useAuth";

function pct(v: number) {
  return `${Math.round(v * 100)}%`;
}

function formatSeconds(s: number) {
  if (s < 60) return `${Math.round(s)}s`;
  return `${Math.round(s / 60)}m ${Math.round(s % 60)}s`;
}

export default function DashboardPage() {
  const { data: me } = useMe();
  const { data: stats } = useDashboardStats();
  const { data: claimsPage } = useClaims({ page: 1, page_size: 8 });

  return (
    <div className="p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-800">
          Good morning, {me?.full_name?.split(" ")[0]} 👋
        </h1>
        <p className="text-slate-500 text-sm mt-1">
          {me?.hospital_name ?? "ProClaim"} · {format(new Date(), "EEEE, d MMMM yyyy")}
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <KPICard
          title="Total Claims"
          value={stats?.total_claims ?? "—"}
          subtitle={`${stats?.claims_this_month ?? 0} this month`}
          icon={FileText}
          iconColor="text-teal-600"
        />
        <KPICard
          title="Avg Processing"
          value={stats ? formatSeconds(stats.avg_processing_seconds) : "—"}
          subtitle="Per document batch"
          icon={Clock}
          iconColor="text-blue-600"
        />
        <KPICard
          title="Acceptance Rate"
          value={stats ? pct(stats.acceptance_rate) : "—"}
          subtitle="Claims paid / submitted"
          icon={CheckCircle2}
          iconColor="text-emerald-600"
          trend={
            stats
              ? { value: "vs 72% last month", positive: stats.acceptance_rate > 0.72 }
              : undefined
          }
        />
        <KPICard
          title="Pending Review"
          value={stats?.pending_review_count ?? "—"}
          subtitle="Need your attention"
          icon={AlertTriangle}
          iconColor="text-amber-600"
        />
      </div>

      {/* Recent Claims */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm">
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
          <h2 className="font-semibold text-slate-800">Recent Claims</h2>
          <Link
            to="/claims"
            className="text-sm text-teal-600 hover:text-teal-700 font-medium flex items-center gap-1"
          >
            View all <ChevronRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-slate-400 uppercase tracking-wide border-b border-slate-100">
                <th className="px-6 py-3 font-medium">Reference</th>
                <th className="px-6 py-3 font-medium">Patient</th>
                <th className="px-6 py-3 font-medium">NHIA ID</th>
                <th className="px-6 py-3 font-medium">Date</th>
                <th className="px-6 py-3 font-medium">Amount</th>
                <th className="px-6 py-3 font-medium">Status</th>
                <th className="px-6 py-3 font-medium"></th>
              </tr>
            </thead>
            <tbody>
              {claimsPage?.items.map((claim) => (
                <tr
                  key={claim.id}
                  className="border-b border-slate-50 hover:bg-slate-50/60 transition-colors"
                >
                  <td className="px-6 py-3 font-mono text-xs text-slate-500">
                    {claim.reference_number}
                  </td>
                  <td className="px-6 py-3 font-medium text-slate-800">
                    {claim.patient_name ?? <span className="text-slate-400">—</span>}
                  </td>
                  <td className="px-6 py-3 text-slate-500">
                    {claim.nhia_id ?? "—"}
                  </td>
                  <td className="px-6 py-3 text-slate-500">
                    {claim.date_of_service ?? "—"}
                  </td>
                  <td className="px-6 py-3 text-slate-700">
                    {claim.total_cost ? `₦${Number(claim.total_cost).toLocaleString()}` : "—"}
                  </td>
                  <td className="px-6 py-3">
                    <ClaimStatusBadge status={claim.status} />
                  </td>
                  <td className="px-6 py-3">
                    <Link
                      to={`/claims/${claim.id}`}
                      className="text-teal-600 hover:text-teal-700 font-medium"
                    >
                      Review →
                    </Link>
                  </td>
                </tr>
              ))}
              {!claimsPage?.items.length && (
                <tr>
                  <td colSpan={7} className="px-6 py-10 text-center text-slate-400 text-sm">
                    No claims yet. Upload your first document to get started.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
