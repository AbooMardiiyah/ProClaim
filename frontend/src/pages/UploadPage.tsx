import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight, Loader2 } from "lucide-react";
import toast from "react-hot-toast";
import FileDropzone from "../components/FileDropzone";
import { useCreateClaim, useTriggerExtraction, useUploadDocuments } from "../hooks/useClaims";

type Step = "upload" | "uploading" | "extracting" | "done";

export default function UploadPage() {
  const navigate = useNavigate();
  const [files, setFiles] = useState<File[]>([]);
  const [step, setStep] = useState<Step>("upload");
  const [claimId, setClaimId] = useState<string | null>(null);

  const createClaim = useCreateClaim();

  const handleStart = async () => {
    if (!files.length) {
      toast.error("Please add at least one document");
      return;
    }

    try {
      setStep("uploading");

      // 1. Create claim shell
      const claim = await createClaim.mutateAsync(undefined);
      setClaimId(claim.id);

      // 2. Upload all files
      const form = new FormData();
      files.forEach((f) => form.append("files", f));

      const { default: api } = await import("../lib/api");
      await api.post(`/claims/${claim.id}/documents`, form, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      toast.success(`${files.length} document${files.length > 1 ? "s" : ""} uploaded`);
      setStep("extracting");

      // 3. Trigger extraction
      await api.post(`/claims/${claim.id}/extract`);
      setStep("done");

      // 4. Navigate to review
      setTimeout(() => navigate(`/claims/${claim.id}`), 600);
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? "Upload failed. Please try again.");
      setStep("upload");
    }
  };

  const isWorking = step === "uploading" || step === "extracting";

  return (
    <div className="p-8 max-w-3xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-800">Upload Documents</h1>
        <p className="text-slate-500 text-sm mt-1">
          Upload outpatient registers, lab reports, pharmacy logs, and billing receipts for one
          patient encounter. ProClaim will extract and consolidate the claim automatically.
        </p>
      </div>

      {/* Document Type Guide */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
        {[
          { label: "Outpatient Register", color: "bg-blue-50 border-blue-200 text-blue-700" },
          { label: "Lab Report", color: "bg-purple-50 border-purple-200 text-purple-700" },
          { label: "Pharmacy Log", color: "bg-amber-50 border-amber-200 text-amber-700" },
          { label: "Billing Receipt", color: "bg-teal-50 border-teal-200 text-teal-700" },
        ].map((t) => (
          <div
            key={t.label}
            className={`text-center text-xs font-medium px-3 py-2.5 rounded-lg border ${t.color}`}
          >
            {t.label}
          </div>
        ))}
      </div>

      {/* Dropzone */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm mb-6">
        <FileDropzone
          files={files}
          onChange={setFiles}
          disabled={isWorking}
        />
      </div>

      {/* Progress indicator */}
      {isWorking && (
        <div className="bg-teal-50 border border-teal-200 rounded-xl p-5 mb-6">
          <div className="flex items-center gap-3">
            <Loader2 className="w-5 h-5 text-teal-600 animate-spin shrink-0" />
            <div>
              <p className="text-sm font-semibold text-teal-700">
                {step === "uploading"
                  ? "Uploading documents…"
                  : "Gemini AI is extracting claim data…"}
              </p>
              <p className="text-xs text-teal-600 mt-0.5">
                {step === "extracting" &&
                  "This usually takes 15–90 seconds. You'll be redirected automatically."}
              </p>
            </div>
          </div>
          {/* Progress bar */}
          <div className="mt-3 h-1.5 bg-teal-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-teal-500 rounded-full transition-all duration-1000"
              style={{ width: step === "uploading" ? "30%" : "75%" }}
            />
          </div>
        </div>
      )}

      {/* Start button */}
      <button
        onClick={handleStart}
        disabled={isWorking || !files.length}
        className="flex items-center gap-2 bg-[#028090] hover:bg-[#026070] disabled:opacity-50 text-white font-semibold px-6 py-3 rounded-xl transition-colors text-sm"
      >
        {isWorking ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            {step === "uploading" ? "Uploading…" : "Extracting…"}
          </>
        ) : (
          <>
            Start Extraction
            <ArrowRight className="w-4 h-4" />
          </>
        )}
      </button>

      <p className="text-xs text-slate-400 mt-3">
        {files.length} file{files.length !== 1 ? "s" : ""} selected ·{" "}
        Powered by Gemini 1.5 Flash
      </p>
    </div>
  );
}
