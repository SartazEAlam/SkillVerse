import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { AITutorDrawer } from '../features/ai-tutor/AITutorDrawer'
import { ActivityContainer } from '../features/activities/ActivityContainer'
import { aiApi } from '../services/aiApi'
import * as activityApi from '../services/activityApi'
import type { ApiLessonDetail } from '../types/catalog'
import type { ActivityDetail } from '../types/activity'

// Mock AuthContext
vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({
    user: {
      id: 'test-user-id',
      email: 'learner@skillverse.dev',
      role: 'learner',
      display_name: 'Test Learner',
    },
    loading: false,
    updateProfile: vi.fn(),
    logout: vi.fn(),
  }),
}))

// Mock aiApi
vi.mock('../services/aiApi', () => ({
  aiApi: {
    askTutor: vi.fn(),
    getActivityHint: vi.fn(),
    getStatus: vi.fn(),
    updatePreference: vi.fn(),
  },
}))

// Mock activityApi
vi.mock('../services/activityApi', () => ({
  fetchActivity: vi.fn(),
  fetchActivityAttempts: vi.fn(),
  submitActivityAttempt: vi.fn(),
}))

const mockLesson: ApiLessonDetail = {
  id: 'lesson-101',
  slug: 'understanding-recursion',
  title: 'Understanding Recursion',
  description: 'Learn recursion with base cases and call stacks.',
  sort_order: 1,
  content_version: 1,
  estimated_minutes: 15,
  learning_objectives: ['Identify base cases', 'Trace recursive calls'],
  blocks: [
    {
      id: 'b-1',
      block_type: 'heading',
      sort_order: 1,
      content: { text: 'Understanding Recursion', level: 1 },
    },
    {
      id: 'b-2',
      block_type: 'text',
      sort_order: 2,
      content: { text: 'A recursive function calls itself until reaching a base condition.' },
    },
  ],
}

const mockActivity: ActivityDetail = {
  id: 'act-101',
  lesson_id: 'lesson-101',
  title: 'Base Case Verification',
  instructions: 'Select the statement that best describes a recursive base condition.',
  activity_type: 'single_choice',
  passing_score: 80,
  max_attempts: 3,
  sort_order: 1,
  created_at: '2026-10-25T10:00:00Z',
  updated_at: '2026-10-25T10:00:00Z',
  configuration: {
    question: 'Why is a base case required in a recursive algorithm?',
    options: [
      { id: 'opt-a', text: 'To prevent infinite recursion and stack overflow' },
      { id: 'opt-b', text: 'To make the function execute asynchronously' },
      { id: 'opt-c', text: 'To allocate more memory on heap' },
    ],
  },
}

describe('Phase 8 — AI Tutor Drawer', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders welcome state, lesson title, and prompt suggestions when opened', () => {
    render(<AITutorDrawer isOpen={true} onClose={vi.fn()} lesson={mockLesson} />)

    expect(screen.getByText('SkillVerse AI Tutor')).toBeInTheDocument()
    expect(screen.getAllByText('Understanding Recursion').length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText(/Pedagogical Lesson Companion/i)).toBeInTheDocument()
    expect(screen.getByText('Can you explain the main goal of this lesson?')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Ask a question about this lesson...')).toBeInTheDocument()
  })

  it('submits user question and renders assistant reply and suggested next questions', async () => {
    vi.mocked(aiApi.askTutor).mockResolvedValueOnce({
      response: 'In recursion, the base condition halts further calls and returns a known value.',
      suggestions: ['Can you trace an example call stack?'],
      lesson_title: 'Understanding Recursion',
      provider: 'mock',
    })

    render(<AITutorDrawer isOpen={true} onClose={vi.fn()} lesson={mockLesson} />)

    const input = screen.getByPlaceholderText('Ask a question about this lesson...')
    fireEvent.change(input, { target: { value: 'Why do we need a base case?' } })
    fireEvent.click(screen.getByLabelText('Send message'))

    await waitFor(() => {
      expect(aiApi.askTutor).toHaveBeenCalledWith({
        lesson_id: 'lesson-101',
        message: 'Why do we need a base case?',
        conversation_history: [],
      })
    })

    await waitFor(() => {
      expect(
        screen.getByText(/In recursion, the base condition halts further calls/i)
      ).toBeInTheDocument()
      expect(screen.getByText('Can you trace an example call stack?')).toBeInTheDocument()
    })
  })

  it('displays rate limit error notice when HTTP 429 occurs', async () => {
    vi.mocked(aiApi.askTutor).mockRejectedValueOnce({
      status: 429,
      code: 'RATE_LIMIT_EXCEEDED',
      message: 'Rate limit exceeded.',
    })

    render(<AITutorDrawer isOpen={true} onClose={vi.fn()} lesson={mockLesson} />)

    const input = screen.getByPlaceholderText('Ask a question about this lesson...')
    fireEvent.change(input, { target: { value: 'What is a stack frame?' } })
    fireEvent.click(screen.getByLabelText('Send message'))

    await waitFor(() => {
      expect(
        screen.getByText(/You have reached the hourly question limit \(30\/hr\)/i)
      ).toBeInTheDocument()
    })
  })

  it('displays opt-out notice banner when user has disabled AI features', async () => {
    vi.mocked(aiApi.askTutor).mockRejectedValueOnce({
      status: 403,
      code: 'AI_FEATURE_OPTED_OUT',
      message: 'AI tutoring is disabled.',
    })

    render(<AITutorDrawer isOpen={true} onClose={vi.fn()} lesson={mockLesson} />)

    const input = screen.getByPlaceholderText('Ask a question about this lesson...')
    fireEvent.change(input, { target: { value: 'Explain recursion please' } })
    fireEvent.click(screen.getByLabelText('Send message'))

    await waitFor(() => {
      expect(
        screen.getByText(/AI Tutoring is opted out in your profile preferences/i)
      ).toBeInTheDocument()
    })
  })
})

describe('Phase 8 — Progressive Hints in ActivityContainer', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(activityApi.fetchActivity).mockResolvedValue(mockActivity)
    vi.mocked(activityApi.fetchActivityAttempts).mockResolvedValue({
      activity_id: 'act-101',
      total_attempts: 0,
      max_attempts: 3,
      can_retry: true,
      attempts: [],
    })
  })

  it('renders "Need a Hint?" button and loads progressive hints sequentially', async () => {
    vi.mocked(aiApi.getActivityHint)
      .mockResolvedValueOnce({
        hint: 'Consider what would happen if a function continued calling itself indefinitely.',
        hint_level: 1,
        provider: 'mock',
      })
      .mockResolvedValueOnce({
        hint: 'A recursive definition must reduce towards a terminating boundary condition.',
        hint_level: 2,
        provider: 'mock',
      })

    render(<ActivityContainer activityId="act-101" initialActivity={mockActivity} />)

    // Button should be visible
    const hintButton = screen.getByRole('button', { name: /Request progressive hint/i })
    expect(hintButton).toHaveTextContent('Need a Hint?')

    // 1. Request Level 1 Hint
    fireEvent.click(hintButton)

    await waitFor(() => {
      expect(aiApi.getActivityHint).toHaveBeenCalledWith({
        activity_id: 'act-101',
        hint_level: 1,
      })
      expect(
        screen.getByText(/Consider what would happen if a function continued/i)
      ).toBeInTheDocument()
      expect(screen.getByText(/Directional Nudge/i)).toBeInTheDocument()
    })

    // Button updates to next hint
    expect(hintButton).toHaveTextContent('Hint (2/3)')

    // 2. Request Level 2 Hint
    fireEvent.click(hintButton)

    await waitFor(() => {
      expect(aiApi.getActivityHint).toHaveBeenCalledWith({
        activity_id: 'act-101',
        hint_level: 2,
      })
      expect(
        screen.getByText(/A recursive definition must reduce towards a terminating boundary/i)
      ).toBeInTheDocument()
      expect(screen.getByText(/Core Principle/i)).toBeInTheDocument()
    })
  })

  it('displays friendly message when hint rate limit is reached', async () => {
    vi.mocked(aiApi.getActivityHint).mockRejectedValueOnce({
      status: 429,
      code: 'RATE_LIMIT_EXCEEDED',
      message: 'Rate limit exceeded.',
    })

    render(<ActivityContainer activityId="act-101" initialActivity={mockActivity} />)

    const hintButton = screen.getByRole('button', { name: /Request progressive hint/i })
    fireEvent.click(hintButton)

    await waitFor(() => {
      expect(
        screen.getByText(/Hourly hint limit reached \(10\/hr\)/i)
      ).toBeInTheDocument()
    })
  })
})
