import { Link } from "react-router-dom";
import { Activity, FileText, Brain, Shield, CheckCircle, ArrowRight } from "lucide-react";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-slate-50">
      {/* ── Header ───────────────────────────────────────────────────────── */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-[#02C39A] flex items-center justify-center">
              <Activity className="w-5 h-5 text-white" />
            </div>
            <span className="text-[#0A2342] font-bold text-xl tracking-tight">
              Pro<span className="text-[#02C39A]">Claim</span>
            </span>
          </Link>
          <div className="flex items-center gap-4">
            <Link
              to="/login"
              className="text-sm font-medium text-slate-600 hover:text-[#028090] transition-colors"
            >
              Sign in
            </Link>
            <Link
              to="/login"
              className="text-sm font-medium bg-[#028090] hover:bg-[#026070] text-white px-4 py-2 rounded-lg transition-colors"
            >
              Get Started
            </Link>
          </div>
        </div>
      </header>

      {/* ── Hero ─────────────────────────────────────────────────────────── */}
      <section className="py-20 lg:py-28 px-6">
        <div className="max-w-5xl mx-auto text-center">
          <h1 className="text-4xl lg:text-6xl font-extrabold text-[#0A2342] leading-tight mb-6">
            NHIA claims processing,<br />
            <span className="text-[#028090]">powered by Gemini AI</span>
          </h1>
          <p className="text-lg text-slate-600 max-w-2xl mx-auto mb-10">
            ProClaim helps Nigerian hospitals upload patient encounter documents,
            extract structured claim data automatically, and guide claims through
            review until submission to HMOs.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              to="/login"
              className="flex items-center gap-2 bg-[#028090] hover:bg-[#026070] text-white font-semibold px-6 py-3 rounded-xl transition-colors"
            >
              Start Processing Claims
              <ArrowRight className="w-4 h-4" />
            </Link>
            <a
              href="#how-it-works"
              className="text-[#028090] font-semibold hover:underline"
            >
              See how it works
            </a>
          </div>
        </div>
      </section>

      {/* ── Features ─────────────────────────────────────────────────────── */}
      <section className="py-16 bg-white px-6">
        <div className="max-w-6xl mx-auto">
          <div className="grid md:grid-cols-3 gap-8">
            <div className="p-6 rounded-2xl border border-slate-200 bg-slate-50">
              <div className="w-12 h-12 rounded-xl bg-blue-50 flex items-center justify-center mb-4">
                <FileText className="w-6 h-6 text-[#028090]" />
              </div>
              <h3 className="text-lg font-bold text-[#0A2342] mb-2">Multi-document upload</h3>
              <p className="text-slate-600 text-sm">
                Upload outpatient registers, lab reports, pharmacy logs, and billing
                receipts for a single patient encounter in one batch.
              </p>
            </div>
            <div className="p-6 rounded-2xl border border-slate-200 bg-slate-50">
              <div className="w-12 h-12 rounded-xl bg-violet-50 flex items-center justify-center mb-4">
                <Brain className="w-6 h-6 text-violet-600" />
              </div>
              <h3 className="text-lg font-bold text-[#0A2342] mb-2">Gemini AI extraction</h3>
              <p className="text-slate-600 text-sm">
                Google Gemini 3.5 Flash reads each document and pulls out patient
                name, NHIA ID, diagnosis, costs, and tariff codes automatically.
              </p>
            </div>
            <div className="p-6 rounded-2xl border border-slate-200 bg-slate-50">
              <div className="w-12 h-12 rounded-xl bg-emerald-50 flex items-center justify-center mb-4">
                <Shield className="w-6 h-6 text-emerald-600" />
              </div>
              <h3 className="text-lg font-bold text-[#0A2342] mb-2">Review workflow</h3>
              <p className="text-slate-600 text-sm">
                Billing officers review extracted fields, fix anything the AI missed,
                and move claims through Extracted → Under Review → Ready → Submitted.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── How it works ─────────────────────────────────────────────────── */}
      <section id="how-it-works" className="py-20 px-6">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl font-bold text-[#0A2342] text-center mb-12">How ProClaim works</h2>
          <div className="space-y-8">
            {[
              {
                step: "1",
                title: "Upload encounter documents",
                desc: "Drag and drop PDFs or images for one patient visit. Multiple documents are merged intelligently.",
              },
              {
                step: "2",
                title: "AI extracts structured data",
                desc: "Gemini reads every document and populates NHIA-aligned fields with confidence scores.",
              },
              {
                step: "3",
                title: "Review and approve",
                desc: "Staff verify extracted values, edit any missing fields, and advance the claim through the workflow.",
              },
              {
                step: "4",
                title: "Export and submit",
                desc: "Download a JSON or CSV export ready for upload to any HMO or NHIA reimbursement portal.",
              },
            ].map((item) => (
              <div key={item.step} className="flex gap-5">
                <div className="w-10 h-10 rounded-full bg-[#028090] text-white flex items-center justify-center font-bold shrink-0">
                  {item.step}
                </div>
                <div>
                  <h3 className="text-lg font-bold text-[#0A2342]">{item.title}</h3>
                  <p className="text-slate-600 text-sm mt-1">{item.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Trust / NHIA aligned ─────────────────────────────────────────── */}
      <section className="py-16 bg-[#0A2342] text-white px-6">
        <div className="max-w-5xl mx-auto text-center">
          <h2 className="text-3xl font-bold mb-6">Built for the Nigerian healthcare system</h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6 mt-10">
            {[
              "NHIA-aligned field schema",
              "Multi-tenant hospital support",
              "Audit trail for every change",
              "Role-based access control",
            ].map((item) => (
              <div key={item} className="flex items-center gap-2 justify-center">
                <CheckCircle className="w-5 h-5 text-[#02C39A] shrink-0" />
                <span className="text-sm font-medium">{item}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Footer ───────────────────────────────────────────────────────── */}
      <footer className="bg-white border-t border-slate-200 py-8 px-6">
        <div className="max-w-6xl mx-auto flex items-center justify-center gap-2">
          <div className="w-6 h-6 rounded bg-[#02C39A] flex items-center justify-center">
            <Activity className="w-4 h-4 text-white" />
          </div>
          <span className="text-[#0A2342] font-bold">ProClaim</span>
        </div>
      </footer>
    </div>
  );
}
