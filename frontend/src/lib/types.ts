export interface Bullet {
  id: string;
  text: string;
  display_order: number;
}

export interface Entity {
  id: string;
  title: string;
  subtitle: string | null;
  date_range: string | null;
  location: string | null;
  bullets: Bullet[];
}

export interface EntityInput {
  section_id: string;
  title: string;
  subtitle?: string | null;
  date_range?: string | null;
  location?: string | null;
  bullets: string[];
}

export interface ImportResponse {
  entities: Entity[];
  skills_added: number;
}

export interface Section {
  id: string;
  name: string;
  display_order: number;
  is_mutable: boolean;
  entities: Entity[];
}

export interface Skill {
  id: string;
  category: string;
  items: string[];
}

export interface Resume {
  id: string;
  filename: string;
  page_limit: number;
  created_at: string;
  sections: Section[];
}

export interface ResumeUploadResponse {
  id: string;
  filename: string;
  sections_count: number;
  entities_count: number;
  bullets_count: number;
  skills_count: number;
}

export interface ExtractedRequirements {
  hard_skills: string[];
  soft_skills: string[];
  domain_keywords: string[];
}

export interface RankedEntity {
  entity_id: string;
  section_name: string;
  title: string;
  subtitle: string | null;
  score: number;
  matching_bullets: string[];
}

export interface JobMatchResponse {
  job_id: string;
  extracted_skills: string[];
  extracted_requirements: ExtractedRequirements;
  ranked_entities: RankedEntity[];
}

export interface SubScores {
  keyword_match: number;
  experience_relevance: number;
  skills_alignment: number;
  presentation_quality: number;
}

export interface ScoringResponse {
  id: string;
  overall_score: number;
  sub_scores: SubScores;
  cover_letter: string | null;
  improvement_ideas: string[];
  created_at: string;
}
