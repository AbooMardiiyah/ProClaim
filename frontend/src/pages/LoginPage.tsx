import { useState } from "react";
import { Activity } from "lucide-react";
import { useLogin, useSignup } from "../hooks/useAuth";
import toast from "react-hot-toast";

type Tab = "login" | "signup";

export default function LoginPage() {
  const [tab, setTab] = useState<Tab>("login");

  // Login state
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [loginError, setLoginError] = useState<string | null>(null);
  const login = useLogin();

  // Signup state
  const [signupName, setSignupName] = useState("");
  const [signupEmail, setSignupEmail] = useState("");
  const [signupHospital, setSignupHospital] = useState("");
  const [signupPassword, setSignupPassword] = useState("");
  const [signupConfirm, setSignupConfirm] = useState("");
  const signup = useSignup();

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError(null);
    login.mutate(
      { email: loginEmail, password: loginPassword },
      {
        onError: (err: any) => {
          const status = err?.response?.status;
          if (status === 401) setLoginError("Incorrect email or password. Please check and try again.");
          else if (status === 403) setLoginError("Your account has been disabled. Contact your admin.");
          else setLoginError("Login failed. Please try again.");
        },
      }
    );
  };

  const handleSignup = (e: React.FormEvent) => {
    e.preventDefault();
    if (signupPassword !== signupConfirm) {
      toast.error("Passwords do not match");
      return;
    }
    signup.mutate(
      { email: signupEmail, password: signupPassword, full_name: signupName, hospital_name: signupHospital },
      {
        onSuccess: () => {
          toast.success("Account created! Please sign in.");
          setTab("login");
          setLoginEmail(signupEmail);
        },
        onError: (e: any) => {
          toast.error(e?.response?.data?.detail ?? "Registration failed");
        },
      }
    );
  };

  return (
    <div className="min-h-screen bg-[#0A2342] flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-xl bg-[#02C39A] flex items-center justify-center">
              <Activity className="w-7 h-7 text-white" />
            </div>
            <span className="text-white font-bold text-3xl tracking-tight">
              Pro<span className="text-[#02C39A]">Claim</span>
            </span>
          </div>
          <p className="text-slate-400 text-sm">
            AI-powered claims processing for Nigerian healthcare
          </p>
        </div>

        {/* Card */}
        <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
          {/* Tabs */}
          <div className="flex border-b border-slate-200">
            <button
              onClick={() => setTab("login")}
              className={`flex-1 py-3 text-sm font-semibold transition-colors ${
                tab === "login"
                  ? "text-[#028090] border-b-2 border-[#028090]"
                  : "text-slate-400 hover:text-slate-600"
              }`}
            >
              Sign In
            </button>
            <button
              onClick={() => setTab("signup")}
              className={`flex-1 py-3 text-sm font-semibold transition-colors ${
                tab === "signup"
                  ? "text-[#028090] border-b-2 border-[#028090]"
                  : "text-slate-400 hover:text-slate-600"
              }`}
            >
              Create Account
            </button>
          </div>

          <div className="p-8">
            {tab === "login" ? (
              <>
                <h1 className="text-xl font-bold text-slate-800 mb-6">Sign in to your account</h1>

                {loginError && (
                  <div className="mb-4 px-4 py-3 bg-red-50 text-red-700 text-sm rounded-lg border border-red-200 space-y-1">
                    <p>{loginError}</p>
                    <p className="text-xs text-red-500">
                      Forgot your password? Ask your admin to reset it, or contact{" "}
                      <span className="font-medium">admin@proclaim.ng</span>.
                    </p>
                  </div>
                )}

                <form onSubmit={handleLogin} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1.5">
                      Email address
                    </label>
                    <input
                      type="email"
                      required
                      value={loginEmail}
                      onChange={(e) => { setLoginEmail(e.target.value); setLoginError(null); }}
                      className="w-full border border-slate-300 rounded-lg px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/40 focus:border-teal-500 transition"
                      placeholder="you@hospital.ng"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1.5">
                      Password
                    </label>
                    <input
                      type="password"
                      required
                      value={loginPassword}
                      onChange={(e) => setLoginPassword(e.target.value)}
                      className="w-full border border-slate-300 rounded-lg px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/40 focus:border-teal-500 transition"
                      placeholder="••••••••"
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={login.isPending}
                    className="w-full bg-[#028090] hover:bg-[#026070] text-white font-semibold py-2.5 px-4 rounded-lg transition-colors disabled:opacity-60 text-sm mt-2"
                  >
                    {login.isPending ? "Signing in…" : "Sign in"}
                  </button>
                </form>
              </>
            ) : (
              <>
                <h1 className="text-xl font-bold text-slate-800 mb-6">Create your workspace</h1>

                <form onSubmit={handleSignup} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1.5">
                      Full name
                    </label>
                    <input
                      type="text"
                      required
                      value={signupName}
                      onChange={(e) => setSignupName(e.target.value)}
                      className="w-full border border-slate-300 rounded-lg px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/40 focus:border-teal-500 transition"
                      placeholder="John Adeyemi"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1.5">
                      Hospital / Facility name
                    </label>
                    <input
                      type="text"
                      required
                      value={signupHospital}
                      onChange={(e) => setSignupHospital(e.target.value)}
                      className="w-full border border-slate-300 rounded-lg px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/40 focus:border-teal-500 transition"
                      placeholder="Lagos General Hospital"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1.5">
                      Email address
                    </label>
                    <input
                      type="email"
                      required
                      value={signupEmail}
                      onChange={(e) => setSignupEmail(e.target.value)}
                      className="w-full border border-slate-300 rounded-lg px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/40 focus:border-teal-500 transition"
                      placeholder="you@hospital.ng"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1.5">
                      Password
                    </label>
                    <input
                      type="password"
                      required
                      minLength={8}
                      value={signupPassword}
                      onChange={(e) => setSignupPassword(e.target.value)}
                      className="w-full border border-slate-300 rounded-lg px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/40 focus:border-teal-500 transition"
                      placeholder="Min. 8 characters"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1.5">
                      Confirm password
                    </label>
                    <input
                      type="password"
                      required
                      value={signupConfirm}
                      onChange={(e) => setSignupConfirm(e.target.value)}
                      className="w-full border border-slate-300 rounded-lg px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/40 focus:border-teal-500 transition"
                      placeholder="••••••••"
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={signup.isPending}
                    className="w-full bg-[#028090] hover:bg-[#026070] text-white font-semibold py-2.5 px-4 rounded-lg transition-colors disabled:opacity-60 text-sm mt-2"
                  >
                    {signup.isPending ? "Creating account…" : "Create account"}
                  </button>
                </form>
              </>
            )}
          </div>
        </div>

        <p className="text-center text-slate-500 text-xs mt-6">
          {tab === "login"
            ? "Need an account? Click Create Account above."
            : "Already have an account? Click Sign In above."}
        </p>

        <div className="text-center mt-3">
          <a href="/" className="text-slate-400 hover:text-slate-200 text-xs transition-colors">
            ← Back to home
          </a>
        </div>
      </div>
    </div>
  );
}
