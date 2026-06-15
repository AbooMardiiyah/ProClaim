/**
 * Inline editable field row used in the Review screen.
 * Shows the extracted value, confidence badge, and an inline edit form.
 */
import { useState } from "react";
import { Check, FileSearch, Pencil, Plus, X } from "lucide-react";
import clsx from "clsx";
import ConfidenceBadge from "./ConfidenceBadge";
import { ClaimField } from "../types";

interface Props {
  field: ClaimField;
  onSave: (fieldKey: string, value: string, note?: string) => void;
  onCite?: (field: ClaimField) => void;
  isCited?: boolean;
  saving?: boolean;
}

export default function FieldEditor({ field, onSave, onCite, isCited, saving }: Props) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(field.value ?? "");
  const [note, setNote] = useState("");

  const isMissing = field.status === "missing";

  const handleSave = () => {
    if (!draft.trim()) return;
    onSave(field.field_key, draft.trim(), note.trim() || undefined);
    setEditing(false);
    setNote("");
  };

  const handleCancel = () => {
    setDraft(field.value ?? "");
    setNote("");
    setEditing(false);
  };

  return (
    <tr className={clsx("border-b border-slate-100 group", isMissing && "bg-red-50/40", isCited && "bg-teal-50/60 ring-1 ring-inset ring-teal-200")}>
      {/* Field label */}
      <td className="py-3 px-4 text-sm font-medium text-slate-700 whitespace-nowrap">
        {field.field_label}
        {/* required indicator */}
      </td>

      {/* Value */}
      <td className="py-3 px-4 text-sm text-slate-800 w-full">
        {editing ? (
          <div className="space-y-2">
            <input
              autoFocus
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleSave();
                if (e.key === "Escape") handleCancel();
              }}
              className="w-full border border-teal-400 rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-teal-400/40"
              placeholder={`Enter ${field.field_label.toLowerCase()}…`}
            />
            <input
              value={note}
              onChange={(e) => setNote(e.target.value)}
              className="w-full border border-slate-200 rounded-md px-3 py-1.5 text-xs text-slate-500 focus:outline-none focus:ring-2 focus:ring-teal-400/30"
              placeholder="Reason for change (optional)"
            />
          </div>
        ) : (
          <span className={clsx(isMissing && "text-slate-400 italic")}>
            {field.value || (isMissing ? "Not extracted" : "—")}
          </span>
        )}
      </td>

      {/* Confidence */}
      <td className="py-3 px-4">
        <ConfidenceBadge score={field.confidence_score} status={field.status} />
      </td>

      {/* Actions */}
      <td className="py-3 px-4 whitespace-nowrap">
        {editing ? (
          <div className="flex items-center gap-1.5">
            <button
              onClick={handleSave}
              disabled={saving || !draft.trim()}
              className="flex items-center gap-1 text-xs bg-teal-600 text-white px-2.5 py-1 rounded-md hover:bg-teal-700 disabled:opacity-50 transition-colors"
            >
              <Check className="w-3 h-3" />
              Save
            </button>
            <button
              onClick={handleCancel}
              className="text-xs text-slate-500 hover:text-slate-700 px-2 py-1 rounded-md transition-colors"
            >
              <X className="w-3 h-3" />
            </button>
          </div>
        ) : (
          <div className="flex items-center gap-1.5">
            {onCite && field.source_document_id && !isMissing && (
              <button
                onClick={() => onCite(field)}
                title="Show source in PDF"
                className={clsx(
                  "flex items-center gap-1 text-xs px-2 py-1 rounded-md transition-colors",
                  isCited
                    ? "bg-teal-100 text-teal-700"
                    : "opacity-0 group-hover:opacity-100 bg-slate-100 text-slate-500 hover:text-teal-600"
                )}
              >
                <FileSearch className="w-3 h-3" />
              </button>
            )}
            <button
              onClick={() => {
                setDraft(field.value ?? "");
                setEditing(true);
              }}
              className={clsx(
                "flex items-center gap-1 text-xs px-2.5 py-1 rounded-md transition-colors opacity-0 group-hover:opacity-100",
                isMissing
                  ? "bg-red-100 text-red-600 hover:bg-red-200 opacity-100"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              )}
            >
              {isMissing ? (
                <>
                  <Plus className="w-3 h-3" /> Add
                </>
              ) : (
                <>
                  <Pencil className="w-3 h-3" /> Edit
                </>
              )}
            </button>
          </div>
        )}
      </td>
    </tr>
  );
}
