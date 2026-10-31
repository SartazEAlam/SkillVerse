/**
 * SkillVerse AI Tutoring & Assistance API Client.
 *
 * Provides typed methods for context-aware lesson tutoring, progressive hints,
 * AI service status checks, and learner opt-out preferences.
 */

import { request } from './api'
import type {
  ActivityHintRequest,
  ActivityHintResponse,
  AIPeriodicPreferenceRequest,
  AIStatusResponse,
  AITutorRequest,
  AITutorResponse,
} from '../types/ai'

export const aiApi = {
  /**
   * Ask the context-aware pedagogical tutor a question grounded in the current lesson.
   */
  async askTutor(data: AITutorRequest, signal?: AbortSignal): Promise<AITutorResponse> {
    return request<AITutorResponse>('/ai/tutor', {
      method: 'POST',
      body: JSON.stringify(data),
      signal,
    })
  },

  /**
   * Request a progressive hint (Levels 1, 2, or 3) for an interactive activity.
   */
  async getActivityHint(data: ActivityHintRequest, signal?: AbortSignal): Promise<ActivityHintResponse> {
    return request<ActivityHintResponse>('/ai/hint', {
      method: 'POST',
      body: JSON.stringify(data),
      signal,
    })
  },

  /**
   * Query the operational status and opt-out state of AI features.
   */
  async getStatus(signal?: AbortSignal): Promise<AIStatusResponse> {
    return request<AIStatusResponse>('/ai/status', {
      method: 'GET',
      signal,
    })
  },

  /**
   * Update the learner's AI opt-out preference.
   */
  async updatePreference(data: AIPeriodicPreferenceRequest, signal?: AbortSignal): Promise<{ opt_out: boolean; message: string }> {
    return request<{ opt_out: boolean; message: string }>('/ai/preferences', {
      method: 'PUT',
      body: JSON.stringify(data),
      signal,
    })
  },
}

