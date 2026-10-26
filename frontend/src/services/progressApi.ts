import { request } from './api'
import type {
  Achievement,
  CoursePrerequisites,
  DashboardSummary,
  Enrollment,
  LessonCompleteResponse,
  LessonProgress,
  RecommendationItem,
  SkillMastery,
} from '../types/progress'

export const progressApi = {
  /**
   * Enroll the authenticated user into an active course version.
   */
  async enroll(courseSlug: string): Promise<Enrollment> {
    return request<Enrollment>(`/courses/${courseSlug}/enroll`, {
      method: 'POST',
    })
  },

  /**
   * Check whether learner satisfies course prerequisites.
   */
  async checkPrerequisites(courseSlug: string): Promise<CoursePrerequisites> {
    return request<CoursePrerequisites>(`/courses/${courseSlug}/prerequisites`)
  },

  /**
   * Fetch all course enrollments for authenticated learner.
   */
  async getEnrollments(): Promise<Enrollment[]> {
    return request<Enrollment[]>('/enrollments')
  },

  /**
   * Fetch single enrollment by ID.
   */
  async getEnrollment(enrollmentId: string): Promise<Enrollment> {
    return request<Enrollment>(`/enrollments/${enrollmentId}`)
  },

  /**
   * Mark lesson started within an enrollment.
   */
  async startLesson(enrollmentId: string, lessonId: string): Promise<LessonProgress> {
    return request<LessonProgress>(`/enrollments/${enrollmentId}/lessons/${lessonId}/start`, {
      method: 'POST',
    })
  },

  /**
   * Mark lesson completed within an enrollment (verified server-side).
   */
  async completeLesson(enrollmentId: string, lessonId: string): Promise<LessonCompleteResponse> {
    return request<LessonCompleteResponse>(`/enrollments/${enrollmentId}/lessons/${lessonId}/complete`, {
      method: 'POST',
    })
  },

  /**
   * Fetch complete consolidated progress dashboard summary.
   */
  async getDashboardSummary(): Promise<DashboardSummary> {
    return request<DashboardSummary>('/progress/dashboard')
  },

  /**
   * Fetch taxonomy skills with user's verified mastery evidence and tiers.
   */
  async getSkillsMastery(): Promise<SkillMastery[]> {
    return request<SkillMastery[]>('/progress/skills')
  },

  /**
   * Fetch all achievements with unlocked status.
   */
  async getAchievements(): Promise<Achievement[]> {
    return request<Achievement[]>('/progress/achievements')
  },

  /**
   * Fetch deterministic next-step recommendations.
   */
  async getRecommendations(): Promise<RecommendationItem[]> {
    return request<RecommendationItem[]>('/progress/recommendations')
  },
}
