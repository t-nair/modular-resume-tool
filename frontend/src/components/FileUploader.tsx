"use client";

import { useCallback, useState } from "react";

interface FileUploaderProps {
  onFileSelect: (file: File) => void;
  accept?: string;
}

export default function FileUploader({ onFileSelect, accept = ".tex" }: FileUploaderProps) {
  const [dragOver, setDragOver] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);

  const handleFile = useCallback(
    (file: File) => {
      setFileName(file.name);
      onFileSelect(file);
    },
    [onFileSelect]
  );

  return (
    <div
      className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
        dragOver ? "border-blue-500 bg-blue-50" : "border-gray-300 hover:border-gray-400"
      }`}
      onDragOver={(e) => {
        e.preventDefault();
        setDragOver(true);
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragOver(false);
        const file = e.dataTransfer.files[0];
        if (file) handleFile(file);
      }}
      onClick={() => {
        const input = document.createElement("input");
        input.type = "file";
        input.accept = accept;
        input.onchange = (e) => {
          const file = (e.target as HTMLInputElement).files?.[0];
          if (file) handleFile(file);
        };
        input.click();
      }}
    >
      {fileName ? (
        <p className="text-green-600 font-medium">{fileName}</p>
      ) : (
        <>
          <p className="text-gray-600 mb-1">Drop your .tex file here or click to browse</p>
          <p className="text-sm text-gray-400">Only .tex files are supported</p>
        </>
      )}
    </div>
  );
}
