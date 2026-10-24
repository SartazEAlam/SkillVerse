/**
 * SkillVerse Phase 4 — Universal Lesson & Structured Content Types.
 *
 * Strongly typed contracts for lesson workspace navigation, block-level content rendering,
 * and presentation boundaries. Aligns with Phase 3 Pydantic schemas.
 */

import type { ApiLessonDetail, ApiModuleDetail, ApiCourseDetail } from './catalog'

// ── Specific Block Content Payloads ────────────────────────────────────────

export interface HeadingBlockContent {
  level: 2 | 3 | 4
  text: string
}

export interface TextBlockContent {
  format: 'markdown' | 'plain'
  text: string
}

export interface ListBlockContent {
  ordered: boolean
  items: string[]
}

export interface CodeExampleBlockContent {
  language: string
  code: string
  caption?: string | null
  show_line_numbers?: boolean
}

export type CalloutVariant = 'info' | 'tip' | 'warning' | 'key_concept'

export interface CalloutBlockContent {
  variant: CalloutVariant
  title?: string | null
  text: string
}

export interface ImageBlockContent {
  url: string
  alt_text: string
  caption?: string | null
}

export interface VideoBlockContent {
  url: string
  title: string
  duration_seconds?: number | null
  transcript_url?: string | null
}

export interface ActivityBlockContent {
  activity_id: string
  title?: string | null
  instructions?: string | null
}

// Discriminated union of strongly typed lesson blocks
export type TypedLessonBlock =
  | { id: string; block_type: 'heading'; content: HeadingBlockContent; sort_order: number }
  | { id: string; block_type: 'text'; content: TextBlockContent; sort_order: number }
  | { id: string; block_type: 'list'; content: ListBlockContent; sort_order: number }
  | { id: string; block_type: 'code_example'; content: CodeExampleBlockContent; sort_order: number }
  | { id: string; block_type: 'callout'; content: CalloutBlockContent; sort_order: number }
  | { id: string; block_type: 'image'; content: ImageBlockContent; sort_order: number }
  | { id: string; block_type: 'video'; content: VideoBlockContent; sort_order: number }
  | { id: string; block_type: 'activity'; content: ActivityBlockContent; sort_order: number }
  | { id: string; block_type: string; content: Record<string, unknown>; sort_order: number }

// ── Lesson Workspace Navigation Models ─────────────────────────────────────

export interface FlattenedLesson {
  id: string
  slug: string
  title: string
  description?: string | null
  moduleId: string
  moduleTitle: string
  moduleOrder: number
  sortOrder: number
  estimatedMinutes?: number | null
  globalIndex: number
}

export interface LessonNavigationContext {
  course: ApiCourseDetail
  modules: ApiModuleDetail[]
  allLessons: FlattenedLesson[]
  currentLesson: ApiLessonDetail
  currentModule: ApiModuleDetail
  currentIndex: number
  totalLessons: number
  prevLesson: FlattenedLesson | null
  nextLesson: FlattenedLesson | null
  isDemo: boolean
}
