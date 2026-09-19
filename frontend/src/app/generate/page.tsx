"use client";

import { useEffect, useState } from "react";
import PdfPreview from "@/components/PdfPreview";
import LoadingSpinner from "@/components/LoadingSpinner";
import { generateTex, generatePdf } from "@/lib/api";

export default function GeneratePage() {
  const [texSource, setTexSource] = useState<string | null>(null);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const resumeId = localStorage.getItem("resumeId");
    const entityIdsJson = localStorage.getItem("selectedEntityIds");

    if (!resumeId || !entityIdsJson) {
      setError("No resume or entities selected. Go back to the match page.");
      setLoading(false);
      return;
    }

    const entityIds = JSON.parse(entityIdsJson) as string[];

    const generate = async () => {
      try {
        // Generate TeX first
        const texResult = await generateTex(resumeId, entityIds);
        setTexSource(texResult.tex_source);

        // Then try PDF
        try {
          const pdfBlob = await generatePdf(resumeId, entityIds);
          const url = URL.createObjectURL(pdfBlob);
          setPdfUrl(url);
        } catch {
          // PDF compilation may fail if Tectonic isn't available - that's OK
          console.warn("PDF compilation failed, showing TeX source only");
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : "Generation failed");
      } finally {
        setLoading(false);
      }
    };

    generate();

    return () => {
      if (pdfUrl) URL.revokeObjectURL(pdfUrl);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (loading) return <LoadingSpinner message="Generating your tailored resume..." />;

  if (error) {
    return (
      <div className="max-w-xl mx-auto">
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Generated Resume</h1>
        <a
          href="/match"
          className="text-sm text-blue-600 hover:underline"
        >
          Back to matching
        </a>
      </div>

      <PdfPreview pdfUrl={pdfUrl} texSource={texSource} />
    </div>
  );
}
