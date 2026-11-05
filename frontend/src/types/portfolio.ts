/**
 * SkillVerse Learner Portfolio & Showcase TypeScript Type Definitions.
 *
 * Reflects backend Pydantic models from app.modules.projects.schemas.
 */

export type PortfolioVisibility = 'PRIVATE' | 'UNLISTED' | 'PUBLIC'

export type PortfolioItemType =
  | 'PROJECT_SUBMISSION'
  | 'SKILL_MASTERY'
  | 'ACHIEVEMENT'
  | 'CUSTOM'

export interface PortfolioArtifact {
  id: string
  original_filename: string
  mime_type: string
  file_size_bytes: number
  download_url: string
}

export interface PortfolioItem {
  id: string
  portfolio_user_id: string
  item_type: PortfolioItemType | string
  reference_id: string | null
  title: string
  summary: string | null
  skills_demonstrated: string[]
  artifacts: PortfolioArtifact[]
  external_url: string | null
  sort_order: number
  visibility: PortfolioVisibility | string
  created_at: string
  updated_at: string
}

export interface PortfolioContactLinks {
  github?: string
  linkedin?: string
  website?: string
  twitter?: string
  [key: string]: string | undefined
}

export interface PortfolioSettings {
  visibility?: string
  theme?: string
  accent?: string
  [key: string]: unknown
}

export interface PortfolioDetail {
  user_id: string
  title: string | null
  headline: string | null
  bio_override: string | null
  custom_slug: string | null
  visibility: PortfolioVisibility | string
  is_public: boolean
  contact_links: PortfolioContactLinks
  settings: PortfolioSettings
  items: PortfolioItem[]
  created_at: string
  updated_at: string
}

export interface PortfolioPublic {
  user_id: string
  display_name: string
  avatar_url: string | null
  title: string | null
  headline: string | null
  bio_override: string | null
  custom_slug: string | null
  visibility: PortfolioVisibility | string
  contact_links: PortfolioContactLinks
  settings: PortfolioSettings
  items: PortfolioItem[]
  created_at: string
}

export interface PortfolioUpdateRequest {
  title?: string | null
  headline?: string | null
  bio_override?: string | null
  description?: string | null
  custom_slug?: string | null
  visibility?: PortfolioVisibility | null
  is_public?: boolean | null
  contact_links?: PortfolioContactLinks | null
  settings?: PortfolioSettings | null
}

export interface PortfolioItemCreateRequest {
  item_type: PortfolioItemType
  reference_id?: string | null
  title?: string | null
  summary?: string | null
  description?: string | null
  visibility?: PortfolioVisibility
  external_url?: string | null
  skills_demonstrated?: string[]
  artifacts?: Array<Record<string, unknown>>
}

export interface PortfolioItemUpdateRequest {
  title?: string | null
  summary?: string | null
  description?: string | null
  visibility?: PortfolioVisibility | null
  external_url?: string | null
  sort_order?: number | null
}

export interface PortfolioItemReorderRequest {
  item_ids: string[]
}

