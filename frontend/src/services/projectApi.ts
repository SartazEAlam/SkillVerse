/**
 * SkillVerse Projects & Submissions API Client.
 *
 * Provides typed methods for project catalog discovery, project specifications,
 * learner submissions lifecycle, artifact uploads, and revision workflows.
 */

import { request } from './api'
import type { ApiDiscipline, ApiSkillDetail } from '../types/catalog'
import type {
  Artifact,
  ArtifactListResponse,
  ProjectDetail,
  ProjectFilterParams,
  ProjectPaginatedResponse,
  SubmissionDetail,
  SubmissionHistoryResponse,
  SubmissionSummary,
} from '../types/project'

export const projectApi = {
  /**
   * Browse published projects in the catalog with pagination, search, and taxonomy filters.
   */
  async listProjects(
    params: ProjectFilterParams = {},
    signal?: AbortSignal
  ): Promise<ProjectPaginatedResponse> {
    const searchParams = new URLSearchParams()
    if (params.search) searchParams.set('search', params.search.trim())
    if (params.discipline_id) searchParams.set('discipline_id', params.discipline_id)
    if (params.skill_id) searchParams.set('skill_id', params.skill_id)
    if (params.difficulty_level) searchParams.set('difficulty_level', params.difficulty_level)
    if (params.sort_by) searchParams.set('sort_by', params.sort_by)
    if (params.sort_order) searchParams.set('sort_order', params.sort_order)
    if (params.page) searchParams.set('page', String(params.page))
    if (params.page_size) searchParams.set('page_size', String(params.page_size))

    const qs = searchParams.toString()
    return request<ProjectPaginatedResponse>(`/projects${qs ? `?${qs}` : ''}`, {
      method: 'GET',
      signal,
    })
  },

  /**
   * Retrieve full project specification, rubric, milestones, and the learner's active submission.
   */
  async getProject(slugOrId: string, signal?: AbortSignal): Promise<ProjectDetail> {
    return request<ProjectDetail>(`/projects/${encodeURIComponent(slugOrId)}`, {
      method: 'GET',
      signal,
    })
  },

  /**
   * Start working on a project or resume an existing active draft.
   */
  async startOrGetSubmission(
    projectId: string,
    data?: {
      title?: string
      summary?: string
      content?: Record<string, unknown>
    },
    signal?: AbortSignal
  ): Promise<SubmissionDetail> {
    return request<SubmissionDetail>(`/projects/${encodeURIComponent(projectId)}/submissions`, {
      method: 'POST',
      body: JSON.stringify(data || {}),
      signal,
    })
  },

  /**
   * Retrieve all submissions authored by the authenticated learner.
   */
  async getMySubmissions(
    projectId?: string,
    signal?: AbortSignal
  ): Promise<SubmissionSummary[]> {
    const qs = projectId ? `?project_id=${encodeURIComponent(projectId)}` : ''
    return request<SubmissionSummary[]>(`/submissions/mine${qs}`, {
      method: 'GET',
      signal,
    })
  },

  /**
   * Retrieve complete submission record, deliverables, evaluation, and artifacts.
   */
  async getSubmission(submissionId: string, signal?: AbortSignal): Promise<SubmissionDetail> {
    return request<SubmissionDetail>(`/submissions/${encodeURIComponent(submissionId)}`, {
      method: 'GET',
      signal,
    })
  },

  /**
   * Update draft deliverables, summary, content, and milestones for an in-progress submission.
   */
  async updateDraftSubmission(
    submissionId: string,
    data: {
      title?: string
      summary?: string
      content?: Record<string, unknown>
      milestones_completed?: string[]
    },
    signal?: AbortSignal
  ): Promise<SubmissionDetail> {
    return request<SubmissionDetail>(`/submissions/${encodeURIComponent(submissionId)}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
      signal,
    })
  },

  /**
   * Submit completed project deliverables, transitioning status from DRAFT to SUBMITTED.
   */
  async submitProject(submissionId: string, signal?: AbortSignal): Promise<SubmissionDetail> {
    return request<SubmissionDetail>(`/submissions/${encodeURIComponent(submissionId)}/submit`, {
      method: 'POST',
      signal,
    })
  },

  /**
   * Initiate a new immutable revision draft for a submission in CHANGES_REQUESTED status.
   */
  async createRevision(
    submissionId: string,
    data?: {
      title?: string
      summary?: string
      content?: Record<string, unknown>
    },
    signal?: AbortSignal
  ): Promise<SubmissionDetail> {
    return request<SubmissionDetail>(
      `/submissions/${encodeURIComponent(submissionId)}/revisions`,
      {
        method: 'POST',
        body: JSON.stringify(data || {}),
        signal,
      }
    )
  },

  /**
   * Retrieve the sequential revision history timeline for a submission.
   */
  async getSubmissionHistory(
    submissionId: string,
    signal?: AbortSignal
  ): Promise<SubmissionHistoryResponse> {
    return request<SubmissionHistoryResponse>(
      `/submissions/${encodeURIComponent(submissionId)}/history`,
      {
        method: 'GET',
        signal,
      }
    )
  },

  /**
   * List all uploaded deliverable artifacts for a submission.
   */
  async listSubmissionArtifacts(
    submissionId: string,
    signal?: AbortSignal
  ): Promise<ArtifactListResponse> {
    return request<ArtifactListResponse>(
      `/submissions/${encodeURIComponent(submissionId)}/artifacts`,
      {
        method: 'GET',
        signal,
      }
    )
  },

  /**
   * Upload a deliverable artifact to a draft submission.
   */
  async uploadArtifact(
    submissionId: string,
    file: File,
    isPublic: boolean = false,
    signal?: AbortSignal
  ): Promise<Artifact> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('is_public', isPublic ? 'true' : 'false')

    return request<Artifact>(`/submissions/${encodeURIComponent(submissionId)}/artifacts`, {
      method: 'POST',
      body: formData,
      signal,
    })
  },

  /**
   * Delete an uploaded artifact from a draft submission.
   */
  async deleteArtifact(artifactId: string, signal?: AbortSignal): Promise<void> {
    return request<void>(`/artifacts/${encodeURIComponent(artifactId)}`, {
      method: 'DELETE',
      signal,
    })
  },

  /**
   * Helper to retrieve active disciplines for filtering.
   */
  async listDisciplines(signal?: AbortSignal): Promise<ApiDiscipline[]> {
    return request<ApiDiscipline[]>('/disciplines', {
      method: 'GET',
      signal,
    })
  },

  /**
   * Helper to retrieve skills for filtering.
   */
  async listSkills(disciplineSlug?: string, signal?: AbortSignal): Promise<ApiSkillDetail[]> {
    const qs = disciplineSlug ? `?discipline=${encodeURIComponent(disciplineSlug)}` : ''
    return request<ApiSkillDetail[]>(`/skills${qs}`, {
      method: 'GET',
      signal,
    })
  },
}

