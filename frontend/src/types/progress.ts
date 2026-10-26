export type EnrollmentStatus = 'ENROLLED' | 'IN_PROGRESS' | 'COMPLETED' | 'DROPPED'

export type LessonProgressStatus = 'NOT_STARTED' | 'IN_PROGRESS' | 'COMPLETED'

export type SkillMasteryStatus =
  | 'NOT_STARTED'
  | 'LEARNING'
  | 'PRACTICING'
  | 'PROVISIONAL'
  | 'MASTERED'
  | 'NEEDS_REVIEW'

export interface Enrollment {
  id: string
  user_id: string
  course_id: string
  course_slug: string
  course_title: string
  course_version_id: string
  version_number: number
  status: EnrollmentStatus
  enrolled_at: string
  last_accessed_at: string | null
  completed_at: string | null
  lessons_total: number
  lessons_completed: number
  progress_percentage: number
}

export interface LessonProgress {
  id: string
  enrollment_id: string
  lesson_id: string
  lesson_slug: string
  lesson_title: string
  status: LessonProgressStatus
  started_at: string | null
  completed_at: string | null
  last_accessed_at: string | null
}

export interface LessonCompleteResponse {
  lesson_progress: LessonProgress
  course_completed: boolean
  course_progress_percentage: number
  lessons_completed: number
  lessons_total: number
}

export interface SkillEvidenceItem {
  attempt_id: string
  activity_id: string
  activity_title: string
  activity_type: string
  score: number
  max_score: number
  passed: boolean
  completed_at: string
}

export interface SkillMastery {
  skill_id: string
  skill_slug: string
  skill_name: string
  discipline_slug: string
  discipline_name: string
  mastery_level: number
  status: SkillMasteryStatus
  verified_attempts_count: number
  distinct_tasks_passed: number
  last_practiced_at: string | null
  evidence: SkillEvidenceItem[]
  prerequisites: string[]
  is_unlocked: boolean
}

export interface Achievement {
  id: string
  slug: string
  name: string
  description: string
  icon: string
  earned: boolean
  earned_at: string | null
}

export interface ResumeLearningItem {
  enrollment_id: string
  course_id: string
  course_slug: string
  course_title: string
  lesson_id: string
  lesson_slug: string
  lesson_title: string
  module_id: string
  module_title: string
  progress_percentage: number
}

export interface RecommendationItem {
  type: 'resume' | 'next_course' | 'review_skill'
  title: string
  reason: string
  course_slug: string | null
  skill_slug: string | null
}

export interface RecentAttemptItem {
  attempt_id: string
  activity_id: string
  activity_title: string
  activity_type: string
  score: number
  max_score: number
  passed: boolean
  completed_at: string
}

export interface PrerequisiteStatusItem {
  skill_id: string
  skill_slug: string
  skill_name: string
  required_status: SkillMasteryStatus
  current_status: SkillMasteryStatus
  satisfied: boolean
}

export interface CoursePrerequisites {
  course_slug: string
  course_title: string
  eligible: boolean
  prerequisites: PrerequisiteStatusItem[]
}

export interface DashboardSummary {
  enrolled_courses: Enrollment[]
  resume_learning: ResumeLearningItem | null
  skills_summary: SkillMastery[]
  recent_attempts: RecentAttemptItem[]
  achievements: Achievement[]
  recommendations: RecommendationItem[]
}
