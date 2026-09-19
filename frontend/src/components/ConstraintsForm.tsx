"use client";

interface ConstraintsFormProps {
  pageLimit: number;
  onPageLimitChange: (limit: number) => void;
}

export default function ConstraintsForm({ pageLimit, onPageLimitChange }: ConstraintsFormProps) {
  return (
    <div className="flex items-center gap-3">
      <label className="text-sm font-medium text-gray-700">Page Limit:</label>
      <select
        value={pageLimit}
        onChange={(e) => onPageLimitChange(Number(e.target.value))}
        className="border border-gray-300 rounded px-3 py-1.5 text-sm"
      >
        <option value={1}>1 page</option>
        <option value={2}>2 pages</option>
        <option value={3}>3 pages</option>
      </select>
    </div>
  );
}
