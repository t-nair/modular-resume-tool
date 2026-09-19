import type { Entity } from "@/lib/types";

interface EntityCardProps {
  entity: Entity;
  selectable?: boolean;
  selected?: boolean;
  onToggle?: (id: string) => void;
  score?: number;
  onEdit?: () => void;
  onDelete?: (id: string) => void;
}

export default function EntityCard({
  entity,
  selectable = false,
  selected = false,
  onToggle,
  score,
  onEdit,
  onDelete,
}: EntityCardProps) {
  return (
    <div
      className={`border rounded-lg p-3 transition-colors ${
        selectable ? "cursor-pointer" : ""
      } ${selected ? "border-blue-500 bg-blue-50" : "border-gray-200"}`}
      onClick={() => selectable && onToggle?.(entity.id)}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="font-medium text-gray-800">{entity.title}</p>
          {entity.subtitle && (
            <p className="text-sm text-gray-600">{entity.subtitle}</p>
          )}
          <div className="flex gap-3 text-xs text-gray-400 mt-0.5">
            {entity.date_range && <span>{entity.date_range}</span>}
            {entity.location && <span>{entity.location}</span>}
          </div>
        </div>
        {score !== undefined && (
          <span className="text-sm font-mono bg-green-100 text-green-700 px-2 py-0.5 rounded">
            {(score * 100).toFixed(0)}%
          </span>
        )}
        {onEdit && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onEdit();
            }}
            className="ml-3 text-xs text-gray-400 hover:text-blue-600"
            aria-label={`Edit ${entity.title}`}
          >
            Edit
          </button>
        )}
        {onDelete && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              if (confirm(`Delete "${entity.title}"?`)) onDelete(entity.id);
            }}
            className="ml-3 text-xs text-gray-400 hover:text-red-600"
            aria-label={`Delete ${entity.title}`}
          >
            Delete
          </button>
        )}
        {selectable && (
          <input
            type="checkbox"
            checked={selected}
            onChange={() => onToggle?.(entity.id)}
            className="ml-3 mt-1"
            onClick={(e) => e.stopPropagation()}
          />
        )}
      </div>
      {entity.bullets.length > 0 && (
        <ul className="mt-2 space-y-1">
          {entity.bullets.map((b) => (
            <li key={b.id} className="text-sm text-gray-600 pl-3 border-l-2 border-gray-200">
              {b.text}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
