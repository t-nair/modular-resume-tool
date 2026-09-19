"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import SectionCard from "@/components/SectionCard";
import ImportPanel from "@/components/ImportPanel";
import LoadingSpinner from "@/components/LoadingSpinner";
import { createSection, deleteEntity, deleteSection, getResume, getSkills } from "@/lib/api";
import type { Resume, Section, Skill } from "@/lib/types";

export default function DashboardPage() {
  const router = useRouter();
  const [resume, setResume] = useState<Resume | null>(null);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(true);
  const [showImport, setShowImport] = useState(false);
  const [newSectionName, setNewSectionName] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async (resumeId: string) => {
    const [r, s] = await Promise.all([getResume(resumeId), getSkills(resumeId)]);
    setResume(r);
    setSkills(s);
  }, []);

  useEffect(() => {
    const resumeId = localStorage.getItem("resumeId");
    if (!resumeId) {
      router.push("/upload");
      return;
    }

    refresh(resumeId)
      .catch(() => router.push("/upload"))
      .finally(() => setLoading(false));
  }, [router, refresh]);

  if (loading) return <LoadingSpinner message="Loading resume..." />;
  if (!resume) return null;

  const reload = () => refresh(resume.id).catch((e) => setError(e.message));

  const handleDeleteEntity = async (entityId: string) => {
    setError(null);
    try {
      await deleteEntity(entityId);
      await reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Delete failed");
    }
  };

  const handleDeleteSection = async (section: Section) => {
    const n = section.entities.length;
    const what = n ? ` and its ${n} ${n === 1 ? "entry" : "entries"}` : "";
    const extra = section.is_mutable ? "" : " It will no longer appear in generated resumes.";
    if (!confirm(`Delete the "${section.name}" section${what}?${extra}`)) return;
    setError(null);
    try {
      await deleteSection(section.id);
      await reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Delete failed");
    }
  };

  const handleCreateSection = async () => {
    if (!newSectionName?.trim()) return;
    setError(null);
    try {
      await createSection(resume.id, newSectionName.trim());
      setNewSectionName(null);
      await reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not add section");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Resume Dashboard</h1>
          <p className="text-sm text-gray-500">
            {resume.filename} &middot; {resume.sections.length} sections &middot;{" "}
            Page limit: {resume.page_limit}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowImport((v) => !v)}
            className="border border-blue-600 text-blue-600 px-4 py-2 rounded text-sm hover:bg-blue-50"
          >
            Import experience
          </button>
          <button
            onClick={() => router.push("/match")}
            className="bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700"
          >
            Match a Job
          </button>
        </div>
      </div>

      {notice && (
        <div className="bg-green-50 border border-green-200 text-green-800 text-sm rounded px-3 py-2 flex justify-between">
          <span>{notice}</span>
          <button onClick={() => setNotice(null)} className="text-green-700">Dismiss</button>
        </div>
      )}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded px-3 py-2">{error}</div>
      )}

      {showImport && (
        <ImportPanel
          resumeId={resume.id}
          sections={resume.sections}
          onImported={async (message) => {
            setShowImport(false);
            setNotice(message);
            await reload();
          }}
          onClose={() => setShowImport(false)}
        />
      )}

      {/* Skills */}
      {skills.length > 0 && (
        <div className="bg-white rounded-lg border p-4">
          <h2 className="font-semibold mb-3">Skills</h2>
          <div className="space-y-2">
            {skills.map((skill) => (
              <div key={skill.id} className="flex gap-2 text-sm">
                <span className="font-medium text-gray-700 min-w-[120px]">
                  {skill.category}:
                </span>
                <span className="text-gray-600">{skill.items.join(", ")}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Sections */}
      <div className="space-y-4">
        {[...resume.sections]
          .sort((a, b) => a.display_order - b.display_order)
          .map((section) => (
            <SectionCard
              key={section.id}
              section={section}
              resumeId={resume.id}
              onChanged={reload}
              onDeleteEntity={handleDeleteEntity}
              onDeleteSection={handleDeleteSection}
            />
          ))}
      </div>

      {/* New section */}
      {newSectionName === null ? (
        <button
          onClick={() => setNewSectionName("")}
          className="text-sm text-blue-600 hover:text-blue-800"
        >
          + Add section
        </button>
      ) : (
        <div className="flex gap-2 items-center">
          <input
            autoFocus
            className="border border-gray-300 rounded px-2 py-1.5 text-sm"
            placeholder="Section name (e.g. Projects)"
            value={newSectionName}
            onChange={(e) => setNewSectionName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleCreateSection()}
          />
          <button
            onClick={handleCreateSection}
            disabled={!newSectionName.trim()}
            className="bg-blue-600 text-white px-3 py-1.5 rounded text-sm hover:bg-blue-700 disabled:opacity-50"
          >
            Add
          </button>
          <button onClick={() => setNewSectionName(null)} className="text-sm text-gray-600">
            Cancel
          </button>
        </div>
      )}
    </div>
  );
}
