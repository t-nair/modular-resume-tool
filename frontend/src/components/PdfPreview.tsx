"use client";

interface PdfPreviewProps {
  pdfUrl: string | null;
  texSource: string | null;
}

export default function PdfPreview({ pdfUrl, texSource }: PdfPreviewProps) {
  return (
    <div className="space-y-4">
      {pdfUrl && (
        <div className="border rounded-lg overflow-hidden">
          <iframe
            src={pdfUrl}
            className="w-full h-[600px]"
            title="PDF Preview"
          />
        </div>
      )}
      {texSource && (
        <details className="border rounded-lg">
          <summary className="px-4 py-2 bg-gray-50 cursor-pointer text-sm font-medium">
            View LaTeX Source
          </summary>
          <pre className="p-4 text-xs overflow-auto max-h-96 bg-gray-900 text-green-400">
            {texSource}
          </pre>
        </details>
      )}
      <div className="flex gap-3">
        {pdfUrl && (
          <a
            href={pdfUrl}
            download="resume.pdf"
            className="bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700"
          >
            Download PDF
          </a>
        )}
        {texSource && (
          <button
            onClick={() => {
              const blob = new Blob([texSource], { type: "text/plain" });
              const url = URL.createObjectURL(blob);
              const a = document.createElement("a");
              a.href = url;
              a.download = "resume.tex";
              a.click();
              URL.revokeObjectURL(url);
            }}
            className="border border-gray-300 px-4 py-2 rounded text-sm hover:bg-gray-50"
          >
            Download .tex
          </button>
        )}
      </div>
    </div>
  );
}
