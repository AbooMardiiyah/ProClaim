import {
  Activity,
  FileText,
  LayoutDashboard,
  LogOut,
  Settings,
  Upload,
} from "lucide-react";
import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import { useLogout, useMe } from "../hooks/useAuth";
import clsx from "clsx";

const NAV = [
  { to: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/upload", icon: Upload, label: "Upload" },
  { to: "/claims", icon: FileText, label: "Claims" },
];

export default function Layout() {
  const { data: me } = useMe();
  const logout = useLogout();

  return (
    <div className="flex h-screen bg-slate-50 font-sans">
      {/* ── Sidebar ─────────────────────────────────────────────────────── */}
      <aside className="w-60 bg-[#0A2342] flex flex-col shrink-0">
        {/* Logo */}
        <div className="px-6 py-5 border-b border-white/10">
          <Link to="/dashboard" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-[#02C39A] flex items-center justify-center">
              <Activity className="w-5 h-5 text-white" />
            </div>
            <span className="text-white font-bold text-xl tracking-tight">
              Pro<span className="text-[#02C39A]">Claim</span>
            </span>
          </Link>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-1">
          {NAV.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) =>
                clsx(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                  isActive
                    ? "bg-[#028090] text-white"
                    : "text-slate-300 hover:bg-white/10 hover:text-white"
                )
              }
            >
              <Icon className="w-4 h-4 shrink-0" />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* User */}
        <div className="px-4 py-4 border-t border-white/10">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-8 h-8 rounded-full bg-[#028090] flex items-center justify-center text-white text-xs font-bold">
              {me?.full_name?.charAt(0) ?? "?"}
            </div>
            <div className="min-w-0">
              <p className="text-white text-sm font-medium truncate">{me?.full_name}</p>
              <p className="text-slate-400 text-xs capitalize">{me?.role?.replace("_", " ")}</p>
            </div>
          </div>
          <button
            onClick={logout}
            className="flex items-center gap-2 text-slate-400 hover:text-white text-xs transition-colors w-full"
          >
            <LogOut className="w-3.5 h-3.5" />
            Sign out
          </button>
        </div>
      </aside>

      {/* ── Main ────────────────────────────────────────────────────────── */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
