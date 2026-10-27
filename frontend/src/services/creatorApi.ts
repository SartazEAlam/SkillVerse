/**
 * SkillVerse Creator Studio API Service.
 *
 * Provides typed methods for course draft authoring, curriculum organization,
 * activity authoring, draft validation, preview, and publication.
 */

import { request } from './api'
import type { ApiCourseDetail, ApiLessonDetail } from '../types/catalog'
import type {
  ActivityAuthoring,
  ActivityCreatePayload,
  ActivityUpdatePayload,
  CourseCreatePayload,
  CourseManagedListResponse,
  CoursePublishResponse,
  CourseUpdatePayload,
  CurriculumReorderPayload,
  DraftValidationResponse,
  LessonCreatePayload,
  LessonContentUpdatePayload,
  LessonUpdatePayload,
  ModuleCreatePayload,
  ModuleUpdatePayload,
} from '../types/creator'

export const creatorApi = {
  /**
   * List all courses managed by the authenticated creator or admin.
   */
  async listManagedCourses(signal?: AbortSignal): Promise<CourseManagedListResponse> {
    return request<CourseManagedListResponse>('/courses/managed', { signal })
  },

  /**
   * Create a new course aggregate and initialize its draft.
   */
  async createCourse(data: CourseCreatePayload, signal?: AbortSignal): Promise<ApiCourseDetail> {
    return request<ApiCourseDetail>('/courses', {
      method: 'POST',
      body: JSON.stringify(data),
      signal,
    })
  },

  /**
   * Retrieve the current working draft of a course.
   */
  async getDraft(courseId: string, signal?: AbortSignal): Promise<ApiCourseDetail> {
    return request<ApiCourseDetail>(`/courses/${courseId}/draft`, { signal })
  },

  /**
   * Update course aggregate metadata.
   */
  async updateCourse(
    courseId: string,
    data: CourseUpdatePayload,
    signal?: AbortSignal
  ): Promise<ApiCourseDetail> {
    return request<ApiCourseDetail>(`/courses/${courseId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
      signal,
    })
  },

  /**
   * Delete an unpublished course.
   */
  async deleteCourse(courseId: string, signal?: AbortSignal): Promise<void> {
    return request<void>(`/courses/${courseId}`, {
      method: 'DELETE',
      signal,
    })
  },

  /**
   * Add a module to the course's working draft.
   */
  async addModule(
    courseId: string,
    data: ModuleCreatePayload,
    signal?: AbortSignal
  ): Promise<{ id: string; title: string; description: string; sort_order: number; lessons: unknown[] }> {
    return request<{ id: string; title: string; description: string; sort_order: number; lessons: unknown[] }>(
      `/courses/${courseId}/draft/modules`,
      {
        method: 'POST',
        body: JSON.stringify(data),
        signal,
      }
    )
  },

  /**
   * Update module details in the draft.
   */
  async updateModule(
    courseId: string,
    moduleId: string,
    data: ModuleUpdatePayload,
    signal?: AbortSignal
  ): Promise<{ id: string; title: string; description: string; sort_order: number }> {
    return request<{ id: string; title: string; description: string; sort_order: number }>(
      `/courses/${courseId}/draft/modules/${moduleId}`,
      {
        method: 'PATCH',
        body: JSON.stringify(data),
        signal,
      }
    )
  },

  /**
   * Delete a module and its lessons from the draft.
   */
  async deleteModule(courseId: string, moduleId: string, signal?: AbortSignal): Promise<void> {
    return request<void>(`/courses/${courseId}/draft/modules/${moduleId}`, {
      method: 'DELETE',
      signal,
    })
  },

  /**
   * Add a lesson to a module in the working draft.
   */
  async addLesson(
    courseId: string,
    moduleId: string,
    data: LessonCreatePayload,
    signal?: AbortSignal
  ): Promise<ApiLessonDetail> {
    return request<ApiLessonDetail>(`/courses/${courseId}/draft/modules/${moduleId}/lessons`, {
      method: 'POST',
      body: JSON.stringify(data),
      signal,
    })
  },

  /**
   * Update lesson outline metadata in the working draft.
   */
  async updateLesson(
    courseId: string,
    lessonId: string,
    data: LessonUpdatePayload,
    signal?: AbortSignal
  ): Promise<ApiLessonDetail> {
    return request<ApiLessonDetail>(`/courses/${courseId}/draft/lessons/${lessonId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
      signal,
    })
  },

  /**
   * Delete a lesson from the working draft.
   */
  async deleteLesson(courseId: string, lessonId: string, signal?: AbortSignal): Promise<void> {
    return request<void>(`/courses/${courseId}/draft/lessons/${lessonId}`, {
      method: 'DELETE',
      signal,
    })
  },

  /**
   * Replace content blocks for a draft lesson.
   */
  async updateLessonContent(
    courseId: string,
    lessonId: string,
    data: LessonContentUpdatePayload,
    signal?: AbortSignal
  ): Promise<ApiLessonDetail> {
    return request<ApiLessonDetail>(`/courses/${courseId}/draft/lessons/${lessonId}/content`, {
      method: 'PUT',
      body: JSON.stringify(data),
      signal,
    })
  },

  /**
   * Batch update curriculum order for modules and lessons.
   */
  async reorderCurriculum(
    courseId: string,
    data: CurriculumReorderPayload,
    signal?: AbortSignal
  ): Promise<{ status: string }> {
    return request<{ status: string }>(`/courses/${courseId}/draft/reorder`, {
      method: 'POST',
      body: JSON.stringify(data),
      signal,
    })
  },

  /**
   * Run comprehensive pre-publication validation against the draft.
   */
  async validateDraft(courseId: string, signal?: AbortSignal): Promise<DraftValidationResponse> {
    return request<DraftValidationResponse>(`/courses/${courseId}/draft/validate`, { signal })
  },

  /**
   * Fetch draft curriculum for authorized preview mode.
   */
  async getDraftPreview(courseId: string, signal?: AbortSignal): Promise<ApiCourseDetail> {
    return request<ApiCourseDetail>(`/courses/${courseId}/draft/preview`, { signal })
  },

  /**
   * Fetch draft lesson details and content blocks for authorized preview mode.
   */
  async getDraftPreviewLesson(
    courseId: string,
    lessonSlug: string,
    signal?: AbortSignal
  ): Promise<ApiLessonDetail> {
    return request<ApiLessonDetail>(`/courses/${courseId}/draft/preview/lessons/${lessonSlug}`, { signal })
  },

  /**
   * Publish the validated working draft into an immutable snapshot.
   */
  async publishCourse(
    courseId: string,
    changelog?: string,
    signal?: AbortSignal
  ): Promise<CoursePublishResponse> {
    return request<CoursePublishResponse>(`/courses/${courseId}/publish`, {
      method: 'POST',
      body: JSON.stringify({ changelog }),
      signal,
    })
  },

  /**
   * Unpublish a course from the public catalog.
   */
  async unpublishCourse(courseId: string, signal?: AbortSignal): Promise<{ id: string; status: string }> {
    return request<{ id: string; status: string }>(`/courses/${courseId}/unpublish`, {
      method: 'POST',
      signal,
    })
  },

  /**
   * Archive a course.
   */
  async archiveCourse(courseId: string, signal?: AbortSignal): Promise<{ id: string; status: string }> {
    return request<{ id: string; status: string }>(`/courses/${courseId}/archive`, {
      method: 'POST',
      signal,
    })
  },

  // ── Activity Authoring ──────────────────────────────────

  /**
   * Create an activity along with its confidential grading configuration.
   */
  async createActivity(data: ActivityCreatePayload, signal?: AbortSignal): Promise<ActivityAuthoring> {
    return request<ActivityAuthoring>('/activities', {
      method: 'POST',
      body: JSON.stringify(data),
      signal,
    })
  },

  /**
   * Retrieve full activity details including answer key for creator authoring.
   */
  async getAuthoringActivity(activityId: string, signal?: AbortSignal): Promise<ActivityAuthoring> {
    return request<ActivityAuthoring>(`/activities/${activityId}/authoring`, { signal })
  },

  /**
   * Update an activity configuration and its grading criteria.
   */
  async updateActivity(
    activityId: string,
    data: ActivityUpdatePayload,
    signal?: AbortSignal
  ): Promise<ActivityAuthoring> {
    return request<ActivityAuthoring>(`/activities/${activityId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
      signal,
    })
  },

  /**
   * Delete an activity from a draft lesson.
   */
  async deleteActivity(activityId: string, signal?: AbortSignal): Promise<void> {
    return request<void>(`/activities/${activityId}`, {
      method: 'DELETE',
      signal,
    })
  },

  /**
   * Fetch disciplines list for course creation.
   */
  async listDisciplines(
    signal?: AbortSignal
  ): Promise<Array<{ id: string; slug: string; name: string; description?: string }>> {
    return request<Array<{ id: string; slug: string; name: string; description?: string }>>(
      '/disciplines',
      { signal }
    )
  },

  /**
   * Fetch skills list for course skill association.
   */
  async listSkills(
    disciplineId?: string,
    signal?: AbortSignal
  ): Promise<Array<{ id: string; slug: string; name: string; discipline_id: string }>> {
    const qs = disciplineId ? `?discipline_id=${encodeURIComponent(disciplineId)}` : ''
    return request<Array<{ id: string; slug: string; name: string; discipline_id: string }>>(
      `/skills${qs}`,
      { signal }
    )
  },
}
