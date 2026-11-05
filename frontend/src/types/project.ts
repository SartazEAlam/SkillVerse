export type ProjectDifficulty = 'BEGINNER' | 'INTERMEDIATE' | 'ADVANCED' | 'EXPERT'

export type SubmissionStatus =
  | 'DRAFT'
  | 'SUBMITTED'
  | 'UNDER_REVIEW'
  | 'EVALUATED'
  | 'COMPLETED'
  | 'CHANGES_REQUESTED'

export interface ProjectSkill {
  skill_id: string
  skill_slug: string
  skill_name: string
  difficulty_level: string
  is_primary: boolean
}

export interface ProjectSummary {
  id: string
  slug: string
  title: string
  short_description: string
  discipline_id: string
  discipline_name?: string | null
  discipline_slug?: string | null
  difficulty_level: ProjectDifficulty
  estimated_duration_hours?: number | null
  status: string
  creator_id: string
  created_at: string
  updated_at: string
  skills: ProjectSkill[]
  submissions_count: number
}

export interface Milestone {
  id: string
  title: string
  description?: string
}

export interface DeliverableItem {
  id?: string
  title: string
  description?: string
  required?: boolean
}

export interface ProjectRequirements {
  milestones?: Milestone[]
  deliverables?: (string | DeliverableItem)[]
  guidelines?: string[] | string
  artifact_limits?: {
    max_files?: number
    max_file_size_mb?: number
    allowed_types?: string[]
  }
  [key: string]: unknown
}

export interface RubricCriterion {
  id: string
  title: string
  description?: string
  max_score: number
  weight?: number
}

export interface EvaluationCriteria {
  passing_score: number
  rubric: RubricCriterion[]
  [key: string]: unknown
}

export interface StarterResource {
  title: string
  url: string
  description?: string
}

export interface ProjectDetail extends ProjectSummary {
  full_description: string
  course_version_id?: string | null
  requirements: ProjectRequirements
  evaluation_criteria: EvaluationCriteria
  starter_resources: StarterResource[]
  creator_name?: string | null
  my_submission?: SubmissionSummary | null
}

export interface ProjectPaginatedResponse {
  items: ProjectSummary[]
  total: number
  page: number
  limit: number
  pages: number
}

export interface Artifact {
  id: string
  submission_id: string
  user_id: string
  storage_key: string
  original_filename: string
  mime_type: string
  file_size_bytes: number
  checksum_sha256: string
  is_public: boolean
  created_at: string
  download_url: string
}

export interface ArtifactListResponse {
  submission_id: string
  total_count: number
  total_size_bytes: number
  artifacts: Artifact[]
}

export interface CriteriaScore {
  criterion_id: string
  score: number
  feedback?: string | null
}

export interface EvaluationResult {
  passing_score: number
  score: number
  passed: boolean
  feedback: string
  criteria_scores?: CriteriaScore[]
  [key: string]: unknown
}

export interface TransitionHistoryItem {
  from_status: string | null
  to_status: string
  timestamp: string
  triggered_by?: string
  reason?: string
}

export interface SubmissionSummary {
  id: string
  project_id: string
  user_id: string
  version_number: number
  revision_of_id?: string | null
  status: SubmissionStatus
  title?: string | null
  score?: number | null
  passed?: boolean | null
  submitted_at?: string | null
  evaluated_at?: string | null
  created_at: string
  updated_at: string
}

export interface SubmissionDetail extends SubmissionSummary {
  summary?: string | null
  content: Record<string, unknown>
  milestones_completed: string[]
  evaluation?: EvaluationResult | null
  evaluator_id?: string | null
  evaluator_name?: string | null
  artifacts: Artifact[]
  revisions_count: number
  transition_history: TransitionHistoryItem[]
}

export interface SubmissionHistoryResponse {
  project_id: string
  user_id: string
  current_version: number
  submissions: SubmissionSummary[]
}

export interface ProjectFilterParams {
  search?: string
  discipline_id?: string
  skill_id?: string
  difficulty_level?: string
  sort_by?: 'created_at' | 'title' | 'difficulty_level'
  sort_order?: 'asc' | 'desc'
  page?: number
  page_size?: number
}

