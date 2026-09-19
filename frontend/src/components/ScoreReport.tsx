"use client";

import type { ScoringResponse } from "@/lib/types";

interface ScoreReportProps {
  result: ScoringResponse;
}

function ScoreGauge({ value, label }: { value: number; label: string }) {
  const percentage = Math.round(value * 100);
  const color =
    percentage >= 70 ? "text-green-600" : percentage >= 40 ? "text-yellow-600" : "text-red-600";

  return (
    <div className="text-center">
      <div className={`text-2xl font-bold ${color}`}>{percentage}%</div>
      <div className="text-xs text-gray-500 mt-1">{label}</div>
    </div>
  );
}

export default function ScoreReport({ result }: ScoreReportProps) {
  return (
    <div className="space-y-6">
      {/* Overall score */}
      <div className="text-center py-6 bg-white rounded-lg border">
        <div className="text-5xl font-bold text-blue-600">
          {Math.round(result.overall_score)}%
        </div>
        <p className="text-gray-500 mt-2">Likelihood of Response</p>
      </div>

      {/* Sub-scores */}
      <div className="grid grid-cols-4 gap-4 bg-white rounded-lg border p-4">
        <ScoreGauge value={result.sub_scores.keyword_match} label="Keyword Match" />
        <ScoreGauge value={result.sub_scores.experience_relevance} label="Experience" />
        <ScoreGauge value={result.sub_scores.skills_alignment} label="Skills" />
        <ScoreGauge value={result.sub_scores.presentation_quality} label="Presentation" />
      </div>

      {/* Cover letter */}
      {result.cover_letter && (
        <div className="bg-white rounded-lg border p-4">
          <h3 className="font-semibold mb-3">Generated Cover Letter</h3>
          <div className="text-sm text-gray-700 whitespace-pre-wrap">
            {result.cover_letter}
          </div>
          <button
            onClick={() => navigator.clipboard.writeText(result.cover_letter!)}
            className="mt-3 text-sm text-blue-600 hover:underline"
          >
            Copy to clipboard
          </button>
        </div>
      )}

      {/* Improvement ideas */}
      {result.improvement_ideas.length > 0 && (
        <div className="bg-white rounded-lg border p-4">
          <h3 className="font-semibold mb-3">Improvement Ideas</h3>
          <ul className="space-y-2">
            {result.improvement_ideas.map((idea, i) => (
              <li key={i} className="text-sm text-gray-700 pl-3 border-l-2 border-blue-200">
                {idea}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
