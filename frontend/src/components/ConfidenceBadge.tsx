import clsx from "clsx";

interface Props {
  score: number | null;
  status: string;
  showLabel?: boolean;
}

export function confidenceColor(score: number | null, status: string) {
  if (status === "missing") return "text-red-500 bg-red-50 border-red-200";
  if (score === null) return "text-slate-400 bg-slate-50 border-slate-200";
  if (score >= 90) return "text-emerald-600 bg-emerald-50 border-emerald-200";
  if (score >= 70) return "text-amber-600 bg-amber-50 border-amber-200";
  return "text-red-500 bg-red-50 border-red-200";
}

export function dotColor(score: number | null, status: string) {
  if (status === "missing") return "bg-red-500";
  if (score === null) return "bg-slate-300";
  if (score >= 90) return "bg-emerald-500";
  if (score >= 70) return "bg-amber-400";
  return "bg-red-500";
}

export default function ConfidenceBadge({ score, status, showLabel = true }: Props) {
  const dot = dotColor(score, status);
  const container = confidenceColor(score, status);

  if (status === "missing") {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold border bg-red-50 text-red-600 border-red-200">
        <span className="w-1.5 h-1.5 rounded-full bg-red-500" />
        MISSING
      </span>
    );
  }

  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border",
        container
      )}
    >
      <span className={clsx("w-1.5 h-1.5 rounded-full", dot)} />
      {showLabel && score !== null ? `${score}%` : status}
    </span>
  );
}
