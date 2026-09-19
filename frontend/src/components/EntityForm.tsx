"use client";

import { useState } from "react";
import type { Entity, EntityInput } from "@/lib/types";

export type EntityFormValues = Omit<EntityInput, "section_id">;

interface EntityFormProps {
  // Prefills the form when editing an existing entity
  initial?: Entity;
  submitLabel: string;
  onSubmit: (values: EntityFormValues) => Promise<void>;
  onCancel: () => void;
}

const inputClass = "w-full border border-gray-300 rounded px-2 py-1.5 text-sm";

export default function EntityForm({ initial, submitLabel, onSubmit, onCancel }: EntityFormProps) {
  const [title, setTitle] = useState(initial?.title ?? "");
  const [subtitle, setSubtitle] = useState(initial?.subtitle ?? "");
  const [dateRange, setDateRange] = useState(initial?.date_range ?? "");
  const [location, setLocation] = useState(initial?.location ?? "");
  const [bullets, setBullets] = useState(
    initial ? [...initial.bullets].sort((a, b) => a.display_order - b.display_order).map((b) => b.text).join("\n") : ""
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    setSaving(true);
    setError(null);
    try {
      await onSubmit({
        title: title.trim(),
        subtitle: subtitle.trim() || null,
        date_range: dateRange.trim() || null,
        location: location.trim() || null,
        // One bullet per line; tolerate pasted "- " / "• " prefixes
        bullets: bullets
          .split("\n")
          .map((b) => b.replace(/^\s*[-•*]\s*/, "").trim())
          .filter(Boolean),
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save entry");
      setSaving(false);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      onClick={(e) => e.stopPropagation()}
      className="border border-blue-200 bg-blue-50/50 rounded-lg p-3 space-y-2"
    >
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        <input className={inputClass} placeholder="Title (e.g. Software Engineer Intern) *" value={title} onChange={(e) => setTitle(e.target.value)} required />
        <input className={inputClass} placeholder="Organization" value={subtitle} onChange={(e) => setSubtitle(e.target.value)} />
        <input className={inputClass} placeholder="Dates (e.g. 06/2025 -- Present)" value={dateRange} onChange={(e) => setDateRange(e.target.value)} />
        <input className={inputClass} placeholder="Location" value={location} onChange={(e) => setLocation(e.target.value)} />
      </div>
      <textarea
        className={`${inputClass} min-h-[120px]`}
        placeholder="Bullets, one per line"
        value={bullets}
        onChange={(e) => setBullets(e.target.value)}
      />
      {error && <p className="text-sm text-red-600">{error}</p>}
      <div className="flex gap-2 justify-end">
        <button type="button" onClick={onCancel} className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-800">
          Cancel
        </button>
        <button
          type="submit"
          disabled={saving || !title.trim()}
          className="bg-blue-600 text-white px-3 py-1.5 rounded text-sm hover:bg-blue-700 disabled:opacity-50"
        >
          {saving ? "Saving..." : submitLabel}
        </button>
      </div>
    </form>
  );
}
