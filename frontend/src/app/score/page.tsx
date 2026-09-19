"use client";

import { useState } from "react";
import ScoreReport from "@/components/ScoreReport";
import LoadingSpinner from "@/components/LoadingSpinner";
import { evaluateResume } from "@/lib/api";
import type { ScoringResponse } from "@/lib/types";

export default function ScorePage() {
  const [result, setResult] = useState<ScoringResponse | null>(null);
  const [coverLetter, setCoverLetter] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const resumeId = typeof window !== "undefined" ? localStorage.getItem("resumeId") : null;
  const jobId = typeof window !== "undefined" ? localStorage.getItem("jobId") : null;

  const handleScore = async () => {
    if (!resumeId || !jobId) {
      setError("Upload a resume and match a job first.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const scoring = await evaluateResume(
        resumeId,
        jobId,
        undefined,
        coverLetter || undefined
      );
      setResult(scoring);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Scoring failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Resume Scoring</h1>

      {!result && (
        <div className="max-w-2xl space-y-4">
          <p className="text-gray-600">
            Evaluate your resume against the matched job description. Optionally
            include an existing cover letter for review.
          </p>
          <textarea
            value={coverLetter}
            onChange={(e) => setCoverLetter(e.target.value)}
            placeholder="Paste existing cover letter (optional)..."
            rows={6}
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm resize-y"
          />
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded text-sm">
              {error}
            </div>
          )}
          <button
            onClick={handleScore}
            disabled={loading || !resumeId || !jobId}
            className="bg-blue-600 text-white px-6 py-2.5 rounded font-medium hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? "Evaluating..." : "Run Evaluation"}
          </button>
          {(!resumeId || !jobId) && (
            <p className="text-sm text-amber-600">
              You need to upload a resume and match a job before scoring.
            </p>
          )}
        </div>
      )}

      {loading && <LoadingSpinner message="Running GPT-4o evaluation..." />}

      {result && <ScoreReport result={result} />}
    </div>
  );
}
