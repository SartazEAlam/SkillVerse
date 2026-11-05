/**
 * SkillVerse Portfolio & Showcase API Client.
 *
 * Provides typed methods for portfolio profile management, item curation,
 * sequential reordering, and privacy-filtered public exploration.
 */

import { request } from './api'
import type {
  PortfolioDetail,
  PortfolioItem,
  PortfolioItemCreateRequest,
  PortfolioItemUpdateRequest,
  PortfolioPublic,
  PortfolioUpdateRequest,
} from '../types/portfolio'
import type { SubmissionSummary } from '../types/project'

export const portfolioApi = {
  /**
   * Retrieve the authenticated learner's complete portfolio profile and items.
   * Auto-creates an initial private draft if this is the learner's first visit.
   */
  async getMyPortfolio(signal?: AbortSignal): Promise<PortfolioDetail> {
    return request<PortfolioDetail>('/portfolios/me', {
      method: 'GET',
      signal,
    })
  },

  /**
   * Update the learner's portfolio profile (title, headline, bio, custom slug, visibility, contact links).
   */
  async updateMyPortfolio(
    data: PortfolioUpdateRequest,
    signal?: AbortSignal
  ): Promise<PortfolioDetail> {
    return request<PortfolioDetail>('/portfolios/me', {
      method: 'PATCH',
      body: JSON.stringify(data),
      signal,
    })
  },

  /**
   * Add a new item to the learner's portfolio (completed project submission or custom achievement).
   */
  async addPortfolioItem(
    data: PortfolioItemCreateRequest,
    signal?: AbortSignal
  ): Promise<PortfolioItem> {
    return request<PortfolioItem>('/portfolios/me/items', {
      method: 'POST',
      body: JSON.stringify(data),
      signal,
    })
  },

  /**
   * Update an existing portfolio item (title, summary, visibility, external URL, sort order).
   */
  async updatePortfolioItem(
    itemId: string,
    data: PortfolioItemUpdateRequest,
    signal?: AbortSignal
  ): Promise<PortfolioItem> {
    return request<PortfolioItem>(`/portfolios/me/items/${encodeURIComponent(itemId)}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
      signal,
    })
  },

  /**
   * Non-destructively remove an item from the portfolio without deleting the underlying submission or files.
   */
  async deletePortfolioItem(itemId: string, signal?: AbortSignal): Promise<void> {
    return request<void>(`/portfolios/me/items/${encodeURIComponent(itemId)}`, {
      method: 'DELETE',
      signal,
    })
  },

  /**
   * Reorder portfolio items sequentially by array of item IDs.
   */
  async reorderPortfolioItems(
    itemIds: string[],
    signal?: AbortSignal
  ): Promise<PortfolioItem[]> {
    return request<PortfolioItem[]>('/portfolios/me/items/reorder', {
      method: 'POST',
      body: JSON.stringify({ item_ids: itemIds }),
      signal,
    })
  },

  /**
   * Retrieve a public or unlisted showcase portfolio by custom slug or user UUID.
   * Authoritatively respects backend privacy: private portfolios return 403.
   */
  async getPublicPortfolio(
    slugOrId: string,
    signal?: AbortSignal
  ): Promise<PortfolioPublic> {
    return request<PortfolioPublic>(`/portfolios/${encodeURIComponent(slugOrId)}`, {
      method: 'GET',
      signal,
    })
  },

  /**
   * Retrieve the authenticated learner's completed submissions that can be featured.
   */
  async getCompletedSubmissions(signal?: AbortSignal): Promise<SubmissionSummary[]> {
    const all = await request<SubmissionSummary[]>('/submissions/mine', {
      method: 'GET',
      signal,
    })
    return all.filter((s) => s.status === 'COMPLETED')
  },
}

