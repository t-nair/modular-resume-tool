"use client";

import type { RankedEntity } from "@/lib/types";

interface EntitySelectorProps {
  entities: RankedEntity[];
  selectedIds: Set<string>;
  onToggle: (id: string) => void;
}

export default function EntitySelector({ entities, selectedIds, onToggle }: EntitySelectorProps) {
  // Group by section
  const grouped = entities.reduce<Record<string, RankedEntity[]>>((acc, e) => {
    (acc[e.section_name] ??= []).push(e);
    return acc;
  }, {});

  return (
    <div className="space-y-6">
      {Object.entries(grouped).map(([sectionName, sectionEntities]) => (
        <div key={sectionName}>
          <h3 className="font-semibold text-gray-700 mb-2">{sectionName}</h3>
          <div className="space-y-2">
            {sectionEntities.map((entity) => (
              <div
                key={entity.entity_id}
                className={`border rounded-lg p-3 cursor-pointer transition-colors ${
                  selectedIds.has(entity.entity_id)
                    ? "border-blue-500 bg-blue-50"
                    : "border-gray-200 hover:border-gray-300"
                }`}
                onClick={() => onToggle(entity.entity_id)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <p className="font-medium">{entity.title}</p>
                    {entity.subtitle && (
                      <p className="text-sm text-gray-500">{entity.subtitle}</p>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-mono bg-green-100 text-green-700 px-2 py-0.5 rounded">
                      {(entity.score * 100).toFixed(0)}%
                    </span>
                    <input
                      type="checkbox"
                      checked={selectedIds.has(entity.entity_id)}
                      onChange={() => onToggle(entity.entity_id)}
                      onClick={(e) => e.stopPropagation()}
                    />
                  </div>
                </div>
                {entity.matching_bullets.length > 0 && (
                  <div className="mt-2 space-y-1">
                    {entity.matching_bullets.slice(0, 2).map((b, i) => (
                      <p key={i} className="text-sm text-gray-500 pl-3 border-l-2 border-gray-200 truncate">
                        {b}
                      </p>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
