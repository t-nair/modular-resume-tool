import type {
  Entity,
  EntityInput,
  ImportResponse,
  JobMatchResponse,
  RankedEntity,
  Resume,
  ResumeUploadResponse,
  Section,
  ScoringResponse,
  Skill,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...(options?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...options?.headers,
    },
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `Request failed: ${res.status}`);
  }

  if (res.status === 204) {
    return undefined as T;
  }

  // Handle PDF responses
  if (res.headers.get("content-type")?.includes("application/pdf")) {
    return (await res.blob()) as unknown as T;
  }

  return res.json();
}

// Flow A: Ingestion
export async function uploadResume(file: File, pageLimit: number): Promise<ResumeUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("page_limit", String(pageLimit));

  return request<ResumeUploadResponse>("/api/resumes/upload", {
    method: "POST",
    body: formData,
  });
}

export async function getResume(resumeId: string): Promise<Resume> {
  return request<Resume>(`/api/resumes/${resumeId}`);
}

export async function getSkills(resumeId: string): Promise<Skill[]> {
  return request<Skill[]>(`/api/resumes/${resumeId}/skills`);
}

// Editing: add to a parsed resume
export async function createSection(resumeId: string, name: string): Promise<Section> {
  return request<Section>(`/api/resumes/${resumeId}/sections`, {
    method: "POST",
    body: JSON.stringify({ name }),
  });
}

export async function addEntity(resumeId: string, entity: EntityInput): Promise<Entity> {
  return request<Entity>(`/api/resumes/${resumeId}/entities`, {
    method: "POST",
    body: JSON.stringify(entity),
  });
}

export async function importExperience(
  resumeId: string,
  text: string,
  sectionId?: string
): Promise<ImportResponse> {
  return request<ImportResponse>(`/api/resumes/${resumeId}/import`, {
    method: "POST",
    body: JSON.stringify({ text, section_id: sectionId || null }),
  });
}

export async function updateEntity(
  entityId: string,
  entity: Omit<EntityInput, "section_id">
): Promise<Entity> {
  return request<Entity>(`/api/entities/${entityId}`, {
    method: "PUT",
    body: JSON.stringify(entity),
  });
}

export async function deleteSection(sectionId: string): Promise<void> {
  return request<void>(`/api/sections/${sectionId}`, { method: "DELETE" });
}

export async function deleteEntity(entityId: string): Promise<void> {
  return request<void>(`/api/entities/${entityId}`, { method: "DELETE" });
}

// Flow B: Matching
export async function matchJob(
  resumeId: string,
  jobText: string,
  title?: string,
  company?: string
): Promise<JobMatchResponse> {
  return request<JobMatchResponse>("/api/jobs/match", {
    method: "POST",
    body: JSON.stringify({
      resume_id: resumeId,
      job_text: jobText,
      title,
      company,
    }),
  });
}

export async function searchEntities(
  resumeId: string,
  query: string,
  topK: number = 10
): Promise<RankedEntity[]> {
  return request<RankedEntity[]>("/api/entities/search", {
    method: "POST",
    body: JSON.stringify({
      resume_id: resumeId,
      query,
      top_k: topK,
    }),
  });
}

// Flow B: Generation
export async function generateTex(
  resumeId: string,
  entityIds: string[],
  includeSkills: boolean = true,
  headerInfo?: Record<string, string>
): Promise<{ tex_source: string }> {
  return request<{ tex_source: string }>("/api/resumes/generate/tex", {
    method: "POST",
    body: JSON.stringify({
      resume_id: resumeId,
      entity_ids: entityIds,
      include_skills: includeSkills,
      header_info: headerInfo,
    }),
  });
}

export async function generatePdf(
  resumeId: string,
  entityIds: string[],
  includeSkills: boolean = true,
  headerInfo?: Record<string, string>
): Promise<Blob> {
  return request<Blob>("/api/resumes/generate/pdf", {
    method: "POST",
    body: JSON.stringify({
      resume_id: resumeId,
      entity_ids: entityIds,
      include_skills: includeSkills,
      header_info: headerInfo,
    }),
  });
}

// Flow C: Scoring
export async function evaluateResume(
  resumeId: string,
  jobId: string,
  resumeTex?: string,
  coverLetter?: string
): Promise<ScoringResponse> {
  return request<ScoringResponse>("/api/scoring/evaluate", {
    method: "POST",
    body: JSON.stringify({
      resume_id: resumeId,
      job_id: jobId,
      resume_tex: resumeTex,
      cover_letter: coverLetter,
    }),
  });
}
