import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { WebPracticeActivity } from '../features/activities/WebPracticeActivity'
import { CommunicationActivity } from '../features/activities/CommunicationActivity'
import { OrderingActivity } from '../features/activities/OrderingActivity'
import { MatchingActivity } from '../features/activities/MatchingActivity'
import { ActivityRenderer } from '../features/activities/ActivityRenderer'
import { aiApi } from '../services/aiApi'
import type { ActivityDetail } from '../types/activity'

// Mock AI API
vi.mock('../services/aiApi', () => ({
  aiApi: {
    getCommunicationFeedback: vi.fn(),
  },
}))

describe('Phase 9 Stage 4 — Specialized Practice Activities & Accessible Simulations', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // ── 1. Web Development Practice Activity ──────────────────────────────────
  describe('WebPracticeActivity', () => {
    const mockMilestones = [
      { id: 'm1', title: 'Component Scaffolding', description: 'Setup JSX layout', required: true },
      { id: 'm2', title: 'Styling & Tokens', description: 'Tailwind styling', required: false },
    ]

    it('renders problem statement, objectives, and milestones', () => {
      const handleChange = vi.fn()
      render(
        <WebPracticeActivity
          problemStatement="Build an accessible button component."
          learningObjectives={['Understand ARIA roles', 'Implement focus states']}
          milestones={mockMilestones}
          submission={{}}
          onChange={handleChange}
        />
      )

      expect(screen.getByText('Build an accessible button component.')).toBeInTheDocument()
      expect(screen.getByText('Understand ARIA roles')).toBeInTheDocument()
      expect(screen.getByText('Component Scaffolding')).toBeInTheDocument()
      expect(screen.getByText('Required')).toBeInTheDocument()
      expect(screen.getByText('Optional')).toBeInTheDocument()
    })

    it('toggles milestone completion on click', () => {
      const handleChange = vi.fn()
      render(
        <WebPracticeActivity
          milestones={mockMilestones}
          submission={{ completed_milestone_ids: ['m1'] }}
          onChange={handleChange}
        />
      )

      const milestoneBtn = screen.getByText('Component Scaffolding').closest('button')
      expect(milestoneBtn).toHaveAttribute('aria-pressed', 'true')

      fireEvent.click(milestoneBtn!)
      // Unchecking m1
      expect(handleChange).toHaveBeenCalledWith(
        expect.objectContaining({ completed_milestone_ids: [] })
      )
    })

    it('validates safe URLs and displays validation alert for unsafe protocol', () => {
      const handleChange = vi.fn()
      render(
        <WebPracticeActivity
          requireRepoUrl={true}
          submission={{ repo_url: 'javascript:alert(1)' }}
          onChange={handleChange}
        />
      )

      expect(
        screen.getByText(/must be a valid http or https repository url/i)
      ).toBeInTheDocument()
    })

    it('updates inputs for repository and reflection', () => {
      const handleChange = vi.fn()
      render(
        <WebPracticeActivity
          submission={{ repo_url: '', reflection: '' }}
          onChange={handleChange}
        />
      )

      const repoInput = screen.getByLabelText(/repository url/i)
      fireEvent.change(repoInput, { target: { value: 'https://github.com/user/component' } })
      expect(handleChange).toHaveBeenCalledWith(
        expect.objectContaining({ repo_url: 'https://github.com/user/component' })
      )

      const reflectionInput = screen.getByLabelText(/technical reflection/i)
      fireEvent.change(reflectionInput, {
        target: { value: 'Using semantic elements improved keyboard navigation greatly.' },
      })
      expect(handleChange).toHaveBeenCalledWith(
        expect.objectContaining({
          reflection: 'Using semantic elements improved keyboard navigation greatly.',
        })
      )
    })
  })

  // ── 2. Communication Practice Activity (BLUF & STAR) ──────────────────────
  describe('CommunicationActivity', () => {
    it('renders BLUF format with scenario, audience, and guidance', () => {
      const handleChange = vi.fn()
      render(
        <CommunicationActivity
          config={{
            format: 'bluf',
            scenario: 'Database primary replica memory threshold alert.',
            audience: 'VP Infrastructure',
            objective: 'Approve maintenance window',
          }}
          submission={{}}
          onChange={handleChange}
        />
      )

      expect(screen.getByText(/database primary replica/i)).toBeInTheDocument()
      expect(screen.getByText('VP Infrastructure')).toBeInTheDocument()
      expect(screen.getByText('Approve maintenance window')).toBeInTheDocument()
      expect(screen.getByText(/bottom line up front \(bluf\)/i)).toBeInTheDocument()
      expect(screen.getByText(/context & supporting facts/i)).toBeInTheDocument()
      expect(screen.getByText(/next steps & clear call to action/i)).toBeInTheDocument()
    })

    it('renders STAR format sections properly', () => {
      const handleChange = vi.fn()
      render(
        <CommunicationActivity
          config={{
            format: 'star',
            scenario: 'Resolved high-priority production regression.',
          }}
          submission={{}}
          onChange={handleChange}
        />
      )

      expect(screen.getByText('Situation')).toBeInTheDocument()
      expect(screen.getByText('Task')).toBeInTheDocument()
      expect(screen.getByText('Action')).toBeInTheDocument()
      expect(screen.getByText('Result')).toBeInTheDocument()
    })

    it('requests AI writing review and displays qualitative feedback card', async () => {
      const handleChange = vi.fn()
      vi.mocked(aiApi.getCommunicationFeedback).mockResolvedValueOnce({
        summary: 'Excellent BLUF structure with clear call to action.',
        strengths: ['Immediate recommendation', 'Quantifiable risk metric'],
        improvements: ['Include exact rollback duration'],
        actionable_tips: ['Keep background context under two sentences'],
        section_feedback: {},
        provider: 'mock',
      })

      render(
        <CommunicationActivity
          activityId="comm-act-1"
          config={{
            format: 'bluf',
            scenario: 'Payment service gateway incident.',
          }}
          submission={{
            sections: {
              bottom_line: 'Requesting immediate failover to backup gateway.',
              context_details: 'Primary gateway has 45% timeout rate.',
              next_steps: 'Approve execution now.',
            },
          }}
          onChange={handleChange}
        />
      )

      const reviewBtn = screen.getByRole('button', { name: /request ai writing review/i })
      fireEvent.click(reviewBtn)

      await waitFor(() => {
        expect(aiApi.getCommunicationFeedback).toHaveBeenCalledWith({
          activity_id: 'comm-act-1',
          sections: {
            bottom_line: 'Requesting immediate failover to backup gateway.',
            context_details: 'Primary gateway has 45% timeout rate.',
            next_steps: 'Approve execution now.',
          },
          reflection: '',
        })
      })

      expect(
        await screen.findByText('Excellent BLUF structure with clear call to action.')
      ).toBeInTheDocument()
      expect(screen.getByText('Immediate recommendation')).toBeInTheDocument()
      expect(screen.getByText('Include exact rollback duration')).toBeInTheDocument()
      expect(screen.getByText('Keep background context under two sentences')).toBeInTheDocument()
    })
  })

  // ── 3. Accessible Ordering Activity ───────────────────────────────────────
  describe('Accessible OrderingActivity', () => {
    const items = [
      { id: 'item-1', text: 'Define problem' },
      { id: 'item-2', text: 'Develop prototype' },
      { id: 'item-3', text: 'Deploy to staging' },
    ]

    it('provides keyboard interaction to move items via Arrow keys', () => {
      const handleChange = vi.fn()
      render(
        <OrderingActivity
          items={items}
          orderedItemIds={['item-1', 'item-2', 'item-3']}
          onChange={handleChange}
        />
      )

      const firstItem = screen.getByLabelText(/position 1 of 3: define problem/i)
      expect(firstItem).toBeInTheDocument()

      // Press ArrowDown to move first item down
      fireEvent.keyDown(firstItem, { key: 'ArrowDown' })
      expect(handleChange).toHaveBeenCalledWith(['item-2', 'item-1', 'item-3'])

      // Press End to move first item to end
      fireEvent.keyDown(firstItem, { key: 'End' })
      expect(handleChange).toHaveBeenCalledWith(['item-2', 'item-3', 'item-1'])
    })

    it('moves item via accessible buttons', () => {
      const handleChange = vi.fn()
      render(
        <OrderingActivity
          items={items}
          orderedItemIds={['item-1', 'item-2', 'item-3']}
          onChange={handleChange}
        />
      )

      const moveDownBtn = screen.getByRole('button', { name: /move define problem down/i })
      fireEvent.click(moveDownBtn)
      expect(handleChange).toHaveBeenCalledWith(['item-2', 'item-1', 'item-3'])
    })
  })

  // ── 4. Accessible Matching Activity ───────────────────────────────────────
  describe('Accessible MatchingActivity', () => {
    const leftItems = [
      { id: 'l1', text: 'HTML' },
      { id: 'l2', text: 'CSS' },
    ]
    const rightItems = [
      { id: 'r1', text: 'Structure' },
      { id: 'r2', text: 'Presentation' },
    ]

    it('renders accessible select dropdowns and shows matched count', () => {
      const handleChange = vi.fn()
      render(
        <MatchingActivity
          leftItems={leftItems}
          rightItems={rightItems}
          pairs={{ l1: 'r1' }}
          onChange={handleChange}
        />
      )

      expect(screen.getByText('1 of 2 Matched')).toBeInTheDocument()

      const cssSelect = screen.getByRole('combobox', { name: /match for css/i })
      fireEvent.change(cssSelect, { target: { value: 'r2' } })
      expect(handleChange).toHaveBeenCalledWith('l2', 'r2')
    })
  })

  // ── 5. ActivityRenderer Integration ───────────────────────────────────────
  describe('ActivityRenderer integration for new types', () => {
    it('dispatches to WebPracticeActivity when activity_type is web_practice', () => {
      const activity: ActivityDetail = {
        id: 'web-act',
        lesson_id: 'les-1',
        activity_type: 'web_practice',
        title: 'Component Build',
        instructions: 'Build and share repo.',
        configuration: {
          problem_statement: 'Build a navbar.',
          require_repo_url: true,
        },
        max_attempts: 3,
        sort_order: 1,
        passing_score: 70,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }

      render(
        <ActivityRenderer
          activity={activity}
          submissionState={{}}
          onSubmissionChange={vi.fn()}
        />
      )

      expect(screen.getByText('Build a navbar.')).toBeInTheDocument()
      expect(screen.getByLabelText(/repository url/i)).toBeInTheDocument()
    })

    it('dispatches to CommunicationActivity when activity_type is communication', () => {
      const activity: ActivityDetail = {
        id: 'comm-act',
        lesson_id: 'les-1',
        activity_type: 'communication',
        title: 'Executive Brief',
        instructions: 'Write a BLUF message.',
        configuration: {
          format: 'bluf',
          scenario: 'Server outage incident.',
        },
        max_attempts: 3,
        sort_order: 1,
        passing_score: 70,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }

      render(
        <ActivityRenderer
          activity={activity}
          submissionState={{}}
          onSubmissionChange={vi.fn()}
        />
      )

      expect(screen.getByText(/server outage incident/i)).toBeInTheDocument()
      expect(screen.getByText('Bottom Line Up Front (BLUF)')).toBeInTheDocument()
    })
  })
})
