"use client";

import { useState } from "react";
import { addEntity, updateEntity } from "@/lib/api";
import type { Section } from "@/lib/types";
import EntityCard from "./EntityCard";
import EntityForm from "./EntityForm";

interface SectionCardProps {
  section: Section;
  // When set, the section is editable (add/edit/delete entries, delete section)
  resumeId?: string;
  onChanged?: () => void;
  onDeleteEntity?: (entityId: string) => void;
  onDeleteSection?: (section: Section) => void;
}

export default function SectionCard({
  section,
  resumeId,
  onChanged,
  onDeleteEntity,
  onDeleteSection,
}: SectionCardProps) {
  const [adding, setAdding] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  // Immutable sections are output from their original LaTeX, so entry edits wouldn't show up
  const editable = !!resumeId && section.is_mutable;

  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      <div className="px-4 py-3 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
        <h3 className="font-semibold text-gray-800">{section.name}</h3>
        <div className="flex items-center gap-3">
          {editable && !adding && (
            <button onClick={() => setAdding(true)} className="text-sm text-blue-600 hover:text-blue-800">
              + Add entry
            </button>
          )}
          {resumeId && onDeleteSection && (
            <button
              onClick={() => onDeleteSection(section)}
              className="text-xs text-gray-400 hover:text-red-600"
              aria-label={`Delete section ${section.name}`}
            >
              Delete section
            </button>
          )}
          <span
            className={`text-xs px-2 py-0.5 rounded-full ${
              section.is_mutable
                ? "bg-blue-100 text-blue-700"
                : "bg-gray-100 text-gray-600"
            }`}
          >
            {section.is_mutable ? "Mutable" : "Immutable"}
          </span>
        </div>
      </div>
      <div className="p-4 space-y-3">
        {adding && resumeId && (
          <EntityForm
            submitLabel="Add entry"
            onSubmit={async (values) => {
              await addEntity(resumeId, { section_id: section.id, ...values });
              setAdding(false);
              onChanged?.();
            }}
            onCancel={() => setAdding(false)}
          />
        )}
        {section.entities.map((entity) =>
          editingId === entity.id ? (
            <EntityForm
              key={entity.id}
              initial={entity}
              submitLabel="Save changes"
              onSubmit={async (values) => {
                await updateEntity(entity.id, values);
                setEditingId(null);
                onChanged?.();
              }}
              onCancel={() => setEditingId(null)}
            />
          ) : (
            <EntityCard
              key={entity.id}
              entity={entity}
              onEdit={editable ? () => setEditingId(entity.id) : undefined}
              onDelete={editable ? onDeleteEntity : undefined}
            />
          )
        )}
        {section.entities.length === 0 && !adding && (
          <p className="text-sm text-gray-400 italic">No entities in this section</p>
        )}
      </div>
    </div>
  );
}
