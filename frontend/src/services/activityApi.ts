import { request } from './api'
import type {
  ActivityDetail,
  ActivitySummary,
  AttemptListResponse,
  AttemptResponse,
} from '../types/activity'

/**
 * Fetch sanitized activity definition for a learner.
 * Answer keys are guaranteed never to be leaked by the backend.
 */
export async function fetchActivity(activityId: string): Promise<ActivityDetail> {
  return request<ActivityDetail>(`/activities/${activityId}`)
}

/**
 * Fetch all activities configured for a lesson with current learner attempt summary.
 */
export async function fetchLessonActivities(lessonId: string): Promise<ActivitySummary[]> {
  return request<ActivitySummary[]>(`/lessons/${lessonId}/activities`)
}

/**
 * Submit an answer attempt for server-authoritative grading and recording.
 */
export async function submitActivityAttempt(
  activityId: string,
  submission: Record<string, any>
): Promise<AttemptResponse> {
  return request<AttemptResponse>(`/activities/${activityId}/attempts`, {
    method: 'POST',
    body: JSON.stringify({ submission }),
  })
}

/**
 * Fetch authenticated learner's attempt history for an activity.
 */
export async function fetchActivityAttempts(activityId: string): Promise<AttemptListResponse> {
  return request<AttemptListResponse>(`/activities/${activityId}/attempts`)
}

/**
 * Fetch detailed result of a specific attempt with authorization check.
 */
export async function fetchAttemptDetail(
  activityId: string,
  attemptId: string
): Promise<AttemptResponse> {
  return request<AttemptResponse>(`/activities/${activityId}/attempts/${attemptId}`)
}
