/**
 * SkillVerse Phase 3 — Backend API Contracts for Cross-Disciplinary Catalog & Content Model.
 *
 * These TypeScript interfaces strictly reflect the Phase 3 backend REST API endpoints:
 *   GET /api/v1/disciplines
 *   GET /api/v1/skills
 *   GET /api/v1/skills/taxonomy/map
 *   GET /api/v1/courses
 *   GET /api/v1/courses/:slug
 */

export type ApiCourseDifficulty = 'BEGINNER' | 'INTERMEDIATE' | 'ADVANCED'
export type ApiSkillDifficulty = 'FOUNDATIONAL' | 'INTERMEDIATE' | 'ADVANCED'
export type ApiCourseStatus = 'DRAFT' | 'PUBLISHED' | 'ARCHIVED'

export interface ApiDiscipline {
  id: string
  slug: string
  name: string
  description?: string | null
  icon?: string | null
  sort_order: number
  is_active: boolean
  created_at: string
  skills_count: number
}

export interface ApiSkillSummary {
  id: string
  slug: string
  name: string
  difficulty_level: ApiSkillDifficulty
  icon?: string | null
  sort_order: number
}

export interface ApiSkillDetail extends ApiSkillSummary {
  description?: string | null
  discipline_id: string
  discipline_slug?: string | null
  discipline_name?: string | null
  parent_skill_id?: string | null
  is_active: boolean
  created_at: string
  prerequisites: ApiSkillSummary[]
  unlocked_skills: ApiSkillSummary[]
  courses_count: number
}

export interface ApiPrerequisiteEdge {
  source: string // Prerequisite skill ID (must be completed first)
  target: string // Dependent skill ID (unlocked by source)
}

export interface ApiSkillMapNode {
  id: string
  slug: string
  name: string
  discipline_slug: string
  difficulty_level: ApiSkillDifficulty
  description?: string | null
  icon?: string | null
}

export interface ApiSkillTaxonomyMapResponse {
  nodes: ApiSkillMapNode[]
  edges: ApiPrerequisiteEdge[]
  disciplines: ApiDiscipline[]
}

// ── Course & Content Contracts ─────────────────────────────────────────────

export interface ApiLessonBlock {
  id: string
  block_type: 'heading' | 'text' | 'list' | 'code_example' | 'callout' | 'image' | 'video' | 'activity'
  content: Record<string, unknown>
  sort_order: number
}

export interface ApiLessonDetail {
  id: string
  slug: string
  title: string
  description?: string | null
  learning_objectives: string[]
  estimated_minutes?: number | null
  sort_order: number
  content_version: number
  blocks: ApiLessonBlock[]
}

export interface ApiModuleDetail {
  id: string
  title: string
  description?: string | null
  sort_order: number
  lessons: ApiLessonDetail[]
}

export interface ApiCourseSummary {
  id: string
  slug: string
  title: string
  short_description: string
  discipline_id: string
  discipline_slug?: string | null
  discipline_name?: string | null
  difficulty_level: ApiCourseDifficulty
  estimated_duration_minutes?: number | null
  cover_image_url?: string | null
  status: ApiCourseStatus
  version_number?: number | null
  skills: ApiSkillSummary[]
}

export interface ApiCoursePaginatedResponse {
  items: ApiCourseSummary[]
  total: number
  page: number
  limit: number
  pages: number
}

export interface ApiCourseDetail extends ApiCourseSummary {
  full_description?: string | null
  creator_id: string
  version_id?: string | null
  published_at?: string | null
  learning_objectives: string[]
  modules: ApiModuleDetail[]
}
