/**
 * SkillVerse Phase 5 — Interactive Activity and Assessment Engine Types.
 *
 * Strongly typed models for activities, answer configurations,
 * learner submissions, server-authoritative grading, and attempt histories.
 */

export type ActivityType =
  | 'single_choice'
  | 'multiple_select'
  | 'short_answer'
  | 'true_false'
  | 'fill_in_the_blank'
  | 'ordering'
  | 'matching'
  | 'code_exercise'
  | 'scenario'

export type AttemptStatus = 'in_progress' | 'submitted' | 'graded' | 'review_required'
export type GradingType = 'exact' | 'partial' | 'pattern' | 'manual'

// ── Configuration Models (Learner Facing) ───────────────────────────────────

export interface OptionItem {
  id: string
  text: string
}

export interface BlankItem {
  id: string
  hint?: string | null
}

export interface MatchingItem {
  id: string
  text: string
}

export interface ScenarioDecision {
  id: string
  title: string
  description: string
}

export interface ActivityDetail {
  id: string
  lesson_id: string | null
  activity_type: ActivityType
  title: string
  instructions: string
  configuration: Record<string, any>
  max_attempts: number | null
  sort_order: number
  passing_score: number
  created_at: string
  updated_at: string
}

export interface ActivitySummary {
  id: string
  lesson_id: string | null
  activity_type: ActivityType
  title: string
  instructions: string
  sort_order: number
  max_attempts: number | null
  passing_score: number
  best_score: number | null
  passed: boolean | null
  attempts_count: number
  can_retry: boolean
}

// ── Submission Payloads ─────────────────────────────────────────────────────

export interface SingleChoiceSubmission {
  selected_option_id: string
}

export interface MultipleSelectSubmission {
  selected_option_ids: string[]
}

export interface TrueFalseSubmission {
  selected_boolean: boolean
}

export interface ShortAnswerSubmission {
  text: string
}

export interface FillBlankSubmission {
  answers: Record<string, string>
}

export interface OrderingSubmission {
  ordered_item_ids: string[]
}

export interface MatchingSubmission {
  pairs: Record<string, string>
}

export interface ScenarioSubmission {
  selected_decision_id: string
}

export interface CodingSubmission {
  code: string
  language?: string
}

export type ActivitySubmission =
  | SingleChoiceSubmission
  | MultipleSelectSubmission
  | TrueFalseSubmission
  | ShortAnswerSubmission
  | FillBlankSubmission
  | OrderingSubmission
  | MatchingSubmission
  | ScenarioSubmission
  | CodingSubmission
  | Record<string, unknown>

// ── Attempt & Grading Feedback Responses ────────────────────────────────────

export interface AttemptFeedback {
  message?: string
  explanation?: string
  status?: string
  is_correct?: boolean
  score_percentage?: number
  breakdown?: Record<string, any>
  details?: any[]
  [key: string]: any
}

export interface AttemptResponse {
  id: string
  user_id: string
  activity_id: string
  attempt_number: number
  status: AttemptStatus
  submission: Record<string, any>
  result: Record<string, any> | null
  score: number | null
  max_score: number
  passed: boolean | null
  feedback: AttemptFeedback | null
  started_at: string
  completed_at: string | null
  can_retry: boolean
  attempts_remaining: number | null
}

export interface AttemptListResponse {
  activity_id: string
  total_attempts: number
  max_attempts: number | null
  can_retry: boolean
  attempts: AttemptResponse[]
}
