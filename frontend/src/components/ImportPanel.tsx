"use client";

import { useState } from "react";
import { importExperience } from "@/lib/api";
import type { Section } from "@/lib/types";

interface ImportPanelProps {
  resumeId: string;
  sections: Section[];
  onImported: (message: string) => void;
  onClose: () => void;
}

export default function ImportPanel({ resumeId, sections, onImported, onClose }: ImportPanelProps) {
  const [text, setText] = useState("");
  const [sectionId, setSectionId] = useState("");
  const [importing, setImporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const mutableSections = sections.filter((s) => s.is_mutable);

  const handleFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) setText(await file.text());
  };

  const handleImport = async () => {
    if (!text.trim()) return;
    setImporting(true);
    setError(null);
    try {
      const result = await importExperience(resumeId, text, sectionId || undefined);
      const n = result.entities.length;
      const parts = [`Imported ${n} ${n === 1 ? "entry" : "entries"}`];
      if (result.skills_added) parts.push(`${result.skills_added} new skills`);
      onImported(parts.join(" and "));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Import failed");
    } finally {
      setImporting(false);
    }
  };

  return (
    <div className="bg-white rounded-lg border border-blue-200 p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold">Import experience</h2>
        <button onClick={onClose} className="text-sm text-gray-500 hover:text-gray-700">
          Close
        </button>
      </div>
      <p className="text-sm text-gray-500">
        Paste a job description of your own role, a LinkedIn experience entry, or LaTeX from another resume
        &mdash; or load a .tex / .txt file. Entries are parsed and added to your resume.
      </p>

      <textarea
        className="w-full border border-gray-300 rounded px-3 py-2 text-sm font-mono min-h-[160px]"
        placeholder={"Software Engineering Intern, Acme Robotics, Seattle WA, Jun 2023 - Aug 2023\n- Wrote ROS2 nodes in C++ for lidar obstacle detection\n- ..."}
        value={text}
        onChange={(e) => setText(e.target.value)}
      />

      <div className="flex flex-wrap items-center gap-3">
        <label className="text-sm text-gray-600">
          <input type="file" accept=".tex,.txt,.md" onChange={handleFile} className="text-sm" />
        </label>
        <label className="text-sm text-gray-600 flex items-center gap-2">
          Add to
          <select
            value={sectionId}
            onChange={(e) => setSectionId(e.target.value)}
            className="border border-gray-300 rounded px-2 py-1 text-sm"
          >
            <option value="">Auto (by section headers, else Experience)</option>
            {mutableSections.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </label>
        <button
          onClick={handleImport}
          disabled={importing || !text.trim()}
          className="ml-auto bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700 disabled:opacity-50"
        >
          {importing ? "Parsing..." : "Import"}
        </button>
      </div>
      {error && <p className="text-sm text-red-600">{error}</p>}
    </div>
  );
}
