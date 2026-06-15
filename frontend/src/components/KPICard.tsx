import clsx from "clsx";
import { LucideIcon } from "lucide-react";

interface Props {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  iconColor?: string;
  trend?: { value: string; positive: boolean };
}

export default function KPICard({
  title,
  value,
  subtitle,
  icon: Icon,
  iconColor = "text-teal-600",
  trend,
}: Props) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
      <div className="flex items-start justify-between mb-3">
        <p className="text-sm text-slate-500 font-medium">{title}</p>
        <div className={clsx("w-9 h-9 rounded-lg flex items-center justify-center bg-slate-50", iconColor)}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
      <p className="text-3xl font-bold text-slate-800 tracking-tight">{value}</p>
      {subtitle && <p className="text-xs text-slate-400 mt-1">{subtitle}</p>}
      {trend && (
        <p className={clsx("text-xs font-medium mt-2", trend.positive ? "text-emerald-600" : "text-red-500")}>
          {trend.positive ? "↑" : "↓"} {trend.value}
        </p>
      )}
    </div>
  );
}
