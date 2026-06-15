import { useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { UploadCloud, X, FileText } from "lucide-react";
import clsx from "clsx";

interface Props {
  files: File[];
  onChange: (files: File[]) => void;
  accept?: string[];
  maxFiles?: number;
  disabled?: boolean;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 ** 2).toFixed(1)} MB`;
}

export default function FileDropzone({
  files,
  onChange,
  accept = ["application/pdf", "image/jpeg", "image/png"],
  maxFiles = 10,
  disabled = false,
}: Props) {
  const onDrop = useCallback(
    (accepted: File[]) => {
      onChange([...files, ...accepted].slice(0, maxFiles));
    },
    [files, onChange, maxFiles]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: Object.fromEntries(accept.map((t) => [t, []])),
    maxFiles,
    disabled,
  });

  const remove = (index: number) => {
    onChange(files.filter((_, i) => i !== index));
  };

  return (
    <div className="space-y-3">
      <div
        {...getRootProps()}
        className={clsx(
          "border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors",
          isDragActive
            ? "border-teal-500 bg-teal-50"
            : "border-slate-300 bg-white hover:border-teal-400 hover:bg-teal-50/30",
          disabled && "opacity-50 cursor-not-allowed"
        )}
      >
        <input {...getInputProps()} />
        <UploadCloud className="mx-auto w-10 h-10 text-slate-400 mb-3" />
        <p className="text-sm font-medium text-slate-700">
          {isDragActive ? "Drop files here…" : "Drag & drop files or click to browse"}
        </p>
        <p className="text-xs text-slate-400 mt-1">
          PDF, JPEG, PNG — up to {maxFiles} files, 50MB each
        </p>
      </div>

      {files.length > 0 && (
        <ul className="space-y-2">
          {files.map((file, i) => (
            <li
              key={i}
              className="flex items-center gap-3 bg-white border border-slate-200 rounded-lg px-4 py-2.5 text-sm"
            >
              <FileText className="w-4 h-4 text-slate-400 shrink-0" />
              <span className="flex-1 truncate font-medium text-slate-700">{file.name}</span>
              <span className="text-slate-400 text-xs shrink-0">{formatBytes(file.size)}</span>
              <button
                onClick={() => remove(i)}
                className="text-slate-400 hover:text-red-500 transition-colors"
                disabled={disabled}
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
