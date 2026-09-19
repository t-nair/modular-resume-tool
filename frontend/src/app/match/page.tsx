"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import EntitySelector from "@/components/EntitySelector";
import SearchBar from "@/components/SearchBar";
import LoadingSpinner from "@/components/LoadingSpinner";
import { matchJob, searchEntities } from "@/lib/api";
import type { JobMatchResponse, RankedEntity } from "@/lib/types";

export default function MatchPage() {
  const router = useRouter();
  const [jobText, setJobText] = useState("");
  const [title, setTitle] = useState("");
  const [company, setCompany] = useState("");
  const [loading, setLoading] = useState(false);
  const [matchResult, setMatchResult] = useState<JobMatchResponse | null>(null);
  const [additionalEntities, setAdditionalEntities] = useState<RankedEntity[]>([]);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [error, setError] = useState<string | null>(null);

  const resumeId = typeof window !== "undefined" ? localStorage.getItem("resumeId") : null;

  const handleMatch = async () => {
    if (!resumeId || !jobText.trim()) return;
    setLoading(true);
    setError(null);

    try {
      const result = await matchJob(resumeId, jobText, title || undefined, company || undefined);
      setMatchResult(result);
      // Auto-select top entities
      const topIds = new Set(result.ranked_entities.slice(0, 5).map((e) => e.entity_id));
      setSelectedIds(topIds);
      localStorage.setItem("jobId", result.job_id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Matching failed");
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (query: string) => {
    if (!resumeId) return;
    try {
      const results = await searchEntities(resumeId, query);
      setAdditionalEntities(results);
    } catch {
      // Silently fail search
    }
  };

  const toggleEntity = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleGenerate = () => {
    localStorage.setItem("selectedEntityIds", JSON.stringify([...selectedIds]));
    router.push("/generate");
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Match Job Description</h1>

      {!matchResult && (
        <div className="space-y-4 max-w-2xl">
          <div className="grid grid-cols-2 gap-4">
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Job title (optional)"
              className="border border-gray-300 rounded px-3 py-2 text-sm"
            />
            <input
              type="text"
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              placeholder="Company (optional)"
              className="border border-gray-300 rounded px-3 py-2 text-sm"
            />
          </div>
          <textarea
            value={jobText}
            onChange={(e) => setJobText(e.target.value)}
            placeholder="Paste the full job description here..."
            rows={12}
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm resize-y"
          />
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded text-sm">
              {error}
            </div>
          )}
          <button
            onClick={handleMatch}
            disabled={!jobText.trim() || loading}
            className="bg-blue-600 text-white px-6 py-2.5 rounded font-medium hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? "Analyzing..." : "Analyze & Match"}
          </button>
        </div>
      )}

      {loading && <LoadingSpinner message="Extracting requirements and matching entities..." />}

      {matchResult && (
        <div className="space-y-6">
          {/* Extracted skills */}
          <div className="bg-white rounded-lg border p-4">
            <h2 className="font-semibold mb-2">Extracted Skills & Requirements</h2>
            <div className="flex flex-wrap gap-2">
              {matchResult.extracted_skills.map((skill) => (
                <span
                  key={skill}
                  className="bg-blue-100 text-blue-700 px-2 py-0.5 rounded text-sm"
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>

          {/* Entity selection */}
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">
              Ranked Entities ({selectedIds.size} selected)
            </h2>
            <button
              onClick={handleGenerate}
              disabled={selectedIds.size === 0}
              className="bg-green-600 text-white px-4 py-2 rounded text-sm hover:bg-green-700 disabled:opacity-50"
            >
              Generate Resume
            </button>
          </div>

          <EntitySelector
            entities={matchResult.ranked_entities}
            selectedIds={selectedIds}
            onToggle={toggleEntity}
          />

          {/* Additional search */}
          <div className="border-t pt-4">
            <h3 className="font-medium mb-2">Search for additional entities</h3>
            <SearchBar onSearch={handleSearch} placeholder="Search your resume entities..." />
            {additionalEntities.length > 0 && (
              <div className="mt-3">
                <EntitySelector
                  entities={additionalEntities}
                  selectedIds={selectedIds}
                  onToggle={toggleEntity}
                />
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
