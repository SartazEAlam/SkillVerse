/**
 * Types for Phase 7 Creator Studio and Course Authoring.
 */

import type { ActivityType, GradingType } from './activity'

export interface CourseManagedSummary {
  id: string
  slug: string
  title: string
  short_description: string
  discipline_id: string
  discipline_slug?: string | null
  discipline_name?: string | null
  difficulty_level: 'BEGINNER' | 'INTERMEDIATE' | 'ADVANCED'
  estimated_duration_minutes?: number | null
  cover_image_url?: string | null
  status: 'DRAFT' | 'PUBLISHED' | 'ARCHIVED'
  creator_id: string
  published_version_number?: number | null
  has_draft: boolean
  draft_version_id?: string | null
  modules_count?: number
  lessons_count?: number
  activities_count?: number
  module_count?: number
  lesson_count?: number
  skills?: { id: string; name: string; slug: string }[]
  created_at: string
  updated_at: string
}

export type ManagedCourseItem = CourseManagedSummary

export interface CourseManagedListResponse {
  items: CourseManagedSummary[]
  courses?: CourseManagedSummary[]
  total: number
}

export interface CourseCreatePayload {
  slug: string
  title: string
  short_description: string
  full_description?: string
  discipline_id: string
  difficulty_level?: 'BEGINNER' | 'INTERMEDIATE' | 'ADVANCED'
  estimated_duration_minutes?: number
  cover_image_url?: string
  learning_objectives?: string[]
  skill_ids?: string[]
}

export interface CourseUpdatePayload {
  title?: string
  short_description?: string
  full_description?: string
  difficulty_level?: 'BEGINNER' | 'INTERMEDIATE' | 'ADVANCED'
  estimated_duration_minutes?: number
  cover_image_url?: string
  learning_objectives?: string[]
  skill_ids?: string[]
}

export interface ModuleCreatePayload {
  title: string
  description?: string
  sort_order?: number
}

export interface ModuleUpdatePayload {
  title?: string
  description?: string
  sort_order?: number
}

export interface LessonCreatePayload {
  slug: string
  title: string
  description?: string
  learning_objectives?: string[]
  estimated_minutes?: number
  sort_order?: number
}

export interface LessonUpdatePayload {
  title?: string
  description?: string
  learning_objectives?: string[]
  estimated_minutes?: number
  sort_order?: number
}

export interface LessonContentUpdatePayload {
  document: {
    schema_version: string
    learning_objectives?: string[]
    blocks: Array<{
      id: string
      type: string
      data: Record<string, unknown>
    }>
    resources?: Array<{
      title: string
      url: string
      description?: string
    }>
  }
}

export interface CurriculumReorderPayload {
  modules?: Array<{ id: string; sort_order: number }>
  lessons?: Array<{ id: string; module_id?: string; sort_order: number }>
}

export interface ValidationErrorItem {
  scope: 'course' | 'module' | 'lesson' | 'activity' | 'skill'
  id?: string | null
  title?: string | null
  message: string
}

export interface DraftValidationResponse {
  valid: boolean
  errors: ValidationErrorItem[]
  warnings: ValidationErrorItem[]
}

export interface CoursePublishResponse {
  course_id: string
  version_id: string
  version_number: number
  published_at: string
  publisher_id: string
  changelog?: string | null
}

export interface ActivityAuthoring {
  id: string
  lesson_id: string | null
  activity_type: ActivityType
  title: string
  instructions: string
  configuration: Record<string, unknown>
  skill_id?: string | null
  skill_slug?: string | null
  max_attempts?: number | null
  sort_order: number
  grading_type: GradingType
  passing_score: number
  answer_key: Record<string, unknown>
  rubric?: Record<string, unknown> | null
  test_cases?: Array<Record<string, unknown>> | null
  feedback_config?: Record<string, unknown> | null
  created_at: string
  updated_at: string
}

export interface ActivityCreatePayload {
  lesson_id: string
  activity_type: ActivityType
  title: string
  instructions: string
  configuration?: Record<string, unknown>
  skill_id?: string
  skill_slug?: string
  max_attempts?: number
  sort_order?: number
  grading_type?: GradingType
  passing_score?: number
  answer_key?: Record<string, unknown>
  rubric?: Record<string, unknown>
  test_cases?: Array<Record<string, unknown>>
  feedback_config?: Record<string, unknown>
}

export interface ActivityUpdatePayload {
  title?: string
  instructions?: string
  configuration?: Record<string, unknown>
  skill_id?: string
  skill_slug?: string
  max_attempts?: number
  sort_order?: number
  grading_type?: GradingType
  passing_score?: number
  answer_key?: Record<string, unknown>
  rubric?: Record<string, unknown>
  test_cases?: Array<Record<string, unknown>>
  feedback_config?: Record<string, unknown>
}
