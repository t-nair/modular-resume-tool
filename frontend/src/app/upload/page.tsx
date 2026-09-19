"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import FileUploader from "@/components/FileUploader";
import ConstraintsForm from "@/components/ConstraintsForm";
import LoadingSpinner from "@/components/LoadingSpinner";
import { uploadResume } from "@/lib/api";

export default function UploadPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [pageLimit, setPageLimit] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);

    try {
      const result = await uploadResume(file, pageLimit);
      localStorage.setItem("resumeId", result.id);
      router.push("/dashboard");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <LoadingSpinner message="Parsing resume... This may take a minute." />;
  }

  return (
    <div className="max-w-xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Upload Your Resume</h1>
      <p className="text-gray-600">
        Upload your master LaTeX (.tex) resume. It will be parsed into modular
        sections, entities, and bullets for tailoring.
      </p>

      <FileUploader onFileSelect={setFile} />
      <ConstraintsForm pageLimit={pageLimit} onPageLimitChange={setPageLimit} />

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded text-sm">
          {error}
        </div>
      )}

      <button
        onClick={handleUpload}
        disabled={!file}
        className="w-full bg-blue-600 text-white py-2.5 rounded font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        Upload & Parse
      </button>
    </div>
  );
}
