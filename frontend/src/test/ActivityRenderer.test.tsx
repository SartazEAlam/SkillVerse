import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { SingleChoiceActivity } from '../features/activities/SingleChoiceActivity'
import { MultipleSelectActivity } from '../features/activities/MultipleSelectActivity'
import { TrueFalseActivity } from '../features/activities/TrueFalseActivity'
import { ShortAnswerActivity } from '../features/activities/ShortAnswerActivity'
import { FillBlankActivity } from '../features/activities/FillBlankActivity'
import { OrderingActivity } from '../features/activities/OrderingActivity'
import { MatchingActivity } from '../features/activities/MatchingActivity'
import { ScenarioActivity } from '../features/activities/ScenarioActivity'
import { CodingActivity } from '../features/activities/CodingActivity'
import { ActivityContainer } from '../features/activities/ActivityContainer'
import { LessonRenderer } from '../features/lessons/LessonRenderer'
import * as activityApi from '../services/activityApi'
import type { ActivityDetail, AttemptResponse } from '../types/activity'
import type { ApiLessonBlock } from '../types/catalog'

// Mock AuthContext
vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({
    user: {
      id: 'test-user-id',
      email: 'learner@skillverse.org',
      role: 'LEARNER',
      is_active: true,
      display_name: 'Test Learner',
    },
    loading: false,
  }),
}))

describe('Phase 5 Activity Component Renderers', () => {
  it('renders SingleChoiceActivity and handles user option selection', () => {
    const handleChange = vi.fn()
    const options = [
      { id: 'opt-main', text: 'Semantic <main> element' },
      { id: 'opt-div', text: 'Generic <div id="main"> element' },
    ]

    render(
      <SingleChoiceActivity
        options={options}
        selectedOptionId={null}
        onChange={handleChange}
      />
    )

    const radioMain = screen.getByLabelText(/semantic <main> element/i)
    expect(radioMain).toBeInTheDocument()
    expect(radioMain).not.toBeChecked()

    fireEvent.click(radioMain)
    expect(handleChange).toHaveBeenCalledWith('opt-main')
  })

  it('renders MultipleSelectActivity and allows toggling checkboxes', () => {
    const handleChange = vi.fn()
    const options = [
      { id: 'opt-1', text: '<header>' },
      { id: 'opt-2', text: '<nav>' },
      { id: 'opt-3', text: '<span>' },
    ]

    render(
      <MultipleSelectActivity
        options={options}
        selectedOptionIds={['opt-1']}
        onChange={handleChange}
      />
    )

    const checkbox1 = screen.getByLabelText(/<header>/i)
    const checkbox2 = screen.getByLabelText(/<nav>/i)

    expect(checkbox1).toBeChecked()
    expect(checkbox2).not.toBeChecked()

    fireEvent.click(checkbox2)
    expect(handleChange).toHaveBeenCalledWith(['opt-1', 'opt-2'])
  })

  it('renders TrueFalseActivity with accessible radio toggles', () => {
    const handleChange = vi.fn()

    render(
      <TrueFalseActivity
        statement="A webpage should have only one visible <main> landmark."
        selectedValue={null}
        onChange={handleChange}
      />
    )

    expect(
      screen.getByText(/a webpage should have only one visible <main> landmark/i)
    ).toBeInTheDocument()

    const trueBtn = screen.getByRole('radio', { name: /true/i })
    const falseBtn = screen.getByRole('radio', { name: /false/i })

    expect(trueBtn).toBeInTheDocument()
    expect(falseBtn).toBeInTheDocument()

    fireEvent.click(trueBtn)
    expect(handleChange).toHaveBeenCalledWith(true)
  })

  it('renders ShortAnswerActivity and enforces character count', () => {
    const handleChange = vi.fn()

    render(
      <ShortAnswerActivity
        prompt="What HTML attribute connects an input to its label element?"
        value="for"
        maxLength={50}
        onChange={handleChange}
      />
    )

    const textarea = screen.getByRole('textbox')
    expect(textarea).toHaveValue('for')
    expect(screen.getByText('3 / 50 chars')).toBeInTheDocument()

    fireEvent.change(textarea, { target: { value: 'htmlFor' } })
    expect(handleChange).toHaveBeenCalledWith('htmlFor')
  })

  it('renders FillBlankActivity with inline blank inputs', () => {
    const handleChange = vi.fn()
    const template = 'Use [b1] for navigation and [b2] for the main article.'
    const blanks = [
      { id: 'b1', hint: 'nav' },
      { id: 'b2', hint: 'main' },
    ]

    render(
      <FillBlankActivity
        template={template}
        blanks={blanks}
        values={{ b1: 'nav' }}
        onChange={handleChange}
      />
    )

    const inputB1 = screen.getByLabelText(/fill blank b1/i)
    const inputB2 = screen.getByLabelText(/fill blank b2/i)

    expect(inputB1).toHaveValue('nav')
    expect(inputB2).toHaveValue('')

    fireEvent.change(inputB2, { target: { value: 'article' } })
    expect(handleChange).toHaveBeenCalledWith('b2', 'article')
  })

  it('renders OrderingActivity with accessible up/down movement buttons', () => {
    const handleChange = vi.fn()
    const items = [
      { id: 'step-1', text: 'Step 1: Plan architecture' },
      { id: 'step-2', text: 'Step 2: Draft semantic HTML' },
      { id: 'step-3', text: 'Step 3: Run axe audit' },
    ]

    render(
      <OrderingActivity
        items={items}
        orderedItemIds={['step-1', 'step-2', 'step-3']}
        onChange={handleChange}
      />
    )

    expect(screen.getByText(/Step 1: Plan architecture/i)).toBeInTheDocument()

    // Move step 2 up
    const moveStep2UpBtn = screen.getByRole('button', {
      name: /move step 2: draft semantic html up/i,
    })
    fireEvent.click(moveStep2UpBtn)
    expect(handleChange).toHaveBeenCalledWith(['step-2', 'step-1', 'step-3'])
  })

  it('renders MatchingActivity with pair dropdown selectors', () => {
    const handleChange = vi.fn()
    const leftItems = [
      { id: 'l1', text: '<header>' },
      { id: 'l2', text: '<footer>' },
    ]
    const rightItems = [
      { id: 'r1', text: 'Introductory banner & logo' },
      { id: 'r2', text: 'Copyright & closing links' },
    ]

    render(
      <MatchingActivity
        leftItems={leftItems}
        rightItems={rightItems}
        pairs={{ l1: 'r1' }}
        onChange={handleChange}
      />
    )

    const selectL2 = screen.getByLabelText(/match for <footer>/i)
    expect(selectL2).toBeInTheDocument()

    fireEvent.change(selectL2, { target: { value: 'r2' } })
    expect(handleChange).toHaveBeenCalledWith('l2', 'r2')
  })

  it('renders ScenarioActivity with professional decision cards', () => {
    const handleChange = vi.fn()
    const decisions = [
      {
        id: 'dec-1',
        title: 'Active listening and acknowledgment',
        description: 'Listen carefully and summarize the concern.',
      },
      {
        id: 'dec-2',
        title: 'Immediate dismissal',
        description: 'Tell the client their concern is invalid.',
      },
    ]

    render(
      <ScenarioActivity
        scenarioText="A stakeholder expressed dissatisfaction with the preliminary wireframe."
        decisions={decisions}
        selectedDecisionId={null}
        onChange={handleChange}
      />
    )

    expect(screen.getByText(/a stakeholder expressed dissatisfaction/i)).toBeInTheDocument()
    const decisionCard = screen.getByLabelText(/active listening and acknowledgment/i)
    fireEvent.click(decisionCard)
    expect(handleChange).toHaveBeenCalledWith('dec-1')
  })

  it('renders CodingActivity with language badge and editor area', () => {
    const handleChange = vi.fn()

    render(
      <CodingActivity
        language="python"
        taskDescription="Write a function to return the square of a number."
        code="def square(x): return x * x"
        onChange={handleChange}
      />
    )

    expect(screen.getByText(/write a function to return the square/i)).toBeInTheDocument()
    expect(screen.getByText('python')).toBeInTheDocument()

    const editor = screen.getByLabelText(/code editor/i)
    expect(editor).toHaveValue('def square(x): return x * x')
  })
})

describe('ActivityContainer Full Assessment Lifecycle', () => {
  const mockActivity: ActivityDetail = {
    id: 'act-mcq-1',
    lesson_id: 'lesson-123',
    activity_type: 'single_choice',
    title: 'HTML Landmark Knowledge Check',
    instructions: 'Select the primary content landmark element.',
    configuration: {
      options: [
        { id: 'opt-main', text: '<main>' },
        { id: 'opt-div', text: '<div>' },
      ],
    },
    max_attempts: 2,
    sort_order: 1,
    passing_score: 70.0,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  }

  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('validates submission locally before dispatching to server', async () => {
    render(
      <ActivityContainer
        activityId="act-mcq-1"
        initialActivity={mockActivity}
      />
    )

    const submitBtn = screen.getByRole('button', { name: /submit answer/i })
    fireEvent.click(submitBtn)

    // Displays local error message
    expect(
      await screen.findByText(/please select an option before submitting/i)
    ).toBeInTheDocument()
  })

  it('submits answer and displays server-authoritative score and retry state', async () => {
    const mockAttemptResponse: AttemptResponse = {
      id: 'att-1',
      user_id: 'test-user-id',
      activity_id: 'act-mcq-1',
      attempt_number: 1,
      status: 'graded',
      submission: { selected_option_id: 'opt-main' },
      result: { is_correct: true },
      score: 100.0,
      max_score: 100.0,
      passed: true,
      feedback: {
        is_correct: true,
        message: 'Correct! Well done.',
        explanation: '<main> represents the dominant content of the <body>.',
      },
      started_at: new Date().toISOString(),
      completed_at: new Date().toISOString(),
      can_retry: true,
      attempts_remaining: 1,
    }

    vi.spyOn(activityApi, 'submitActivityAttempt').mockResolvedValue(mockAttemptResponse)

    render(
      <ActivityContainer
        activityId="act-mcq-1"
        initialActivity={mockActivity}
      />
    )

    // Select the option
    const option = screen.getByLabelText(/<main>/i)
    fireEvent.click(option)

    // Click submit
    const submitBtn = screen.getByRole('button', { name: /submit answer/i })
    fireEvent.click(submitBtn)

    // Expect server feedback
    await waitFor(() => {
      expect(screen.getByText('100%')).toBeInTheDocument()
      expect(screen.getByText('Correct! Well done.')).toBeInTheDocument()
      expect(
        screen.getByText(/<main> represents the dominant content of the <body>/i)
      ).toBeInTheDocument()
    })

    // Expect retry button to appear since can_retry is true
    const retryBtn = screen.getByRole('button', { name: /retry activity/i })
    expect(retryBtn).toBeInTheDocument()

    // Clicking retry resets latest attempt view for new input
    fireEvent.click(retryBtn)
    expect(screen.getByRole('button', { name: /submit answer/i })).toBeInTheDocument()
  })

  it('renders embedded activity block in LessonRenderer', async () => {
    const blocks: ApiLessonBlock[] = [
      {
        id: 'heading-1',
        block_type: 'heading',
        content: { level: 2, text: 'Document Landmarks' },
        sort_order: 1,
      },
      {
        id: 'act-block-1',
        block_type: 'activity',
        content: {
          activity_id: 'act-mcq-1',
          title: 'Embedded Landmark Challenge',
          instructions: 'Choose the landmark element.',
        },
        sort_order: 2,
      },
    ]

    vi.spyOn(activityApi, 'fetchActivity').mockResolvedValue(mockActivity)

    render(<LessonRenderer blocks={blocks} />)

    expect(screen.getByRole('heading', { name: /document landmarks/i })).toBeInTheDocument()
    await waitFor(() => {
      expect(screen.getByText('Embedded Landmark Challenge')).toBeInTheDocument()
    })
  })
})
