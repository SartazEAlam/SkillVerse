import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { progressApi } from '../services/progressApi'
import { DashboardPage } from '../pages/DashboardPage'
import { CourseOverviewPage } from '../pages/CourseOverviewPage'
import type { DashboardSummary, Enrollment, CoursePrerequisites } from '../types/progress'
import type { User } from '../types/auth'

// Mock progressApi
vi.mock('../services/progressApi', () => ({
  progressApi: {
    enroll: vi.fn(),
    checkPrerequisites: vi.fn(),
    getEnrollments: vi.fn(),
    getEnrollment: vi.fn(),
    startLesson: vi.fn(),
    completeLesson: vi.fn(),
    getDashboardSummary: vi.fn(),
    getSkillsMastery: vi.fn(),
    getAchievements: vi.fn(),
    getRecommendations: vi.fn(),
  },
}))

// Mock useAuth
const mockUser: User = {
  id: 'user-123',
  email: 'learner@example.com',
  role: 'learner',
  email_verified: true,
  created_at: '2026-10-25T00:00:00Z',
  display_name: 'Elena Rostova',
  bio: 'Software engineer & cross-disciplinary learner',
  avatar_url: null,
  timezone: 'UTC',
}

let mockAuthUser: User | null = mockUser

vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({
    user: mockAuthUser,
    loading: false,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    updateProfile: vi.fn(),
    refreshUser: vi.fn(),
  }),
  AuthProvider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}))

const sampleEnrollment: Enrollment = {
  id: 'enr-1',
  user_id: 'user-123',
  course_id: 'course-web-dev',
  course_slug: 'web-dev-foundations',
  course_title: 'Web Development Foundations',
  course_version_id: 'ver-1',
  version_number: 1,
  status: 'IN_PROGRESS',
  enrolled_at: '2026-10-25T10:00:00Z',
  last_accessed_at: '2026-10-25T11:00:00Z',
  completed_at: null,
  lessons_total: 9,
  lessons_completed: 3,
  progress_percentage: 33.3,
}

const sampleDashboard: DashboardSummary = {
  enrolled_courses: [sampleEnrollment],
  resume_learning: {
    enrollment_id: 'enr-1',
    course_id: 'course-web-dev',
    course_slug: 'web-dev-foundations',
    course_title: 'Web Development Foundations',
    lesson_id: 'les-4',
    lesson_slug: 'flexbox-alignment',
    lesson_title: 'Flexbox Alignment & Spacing',
    module_id: 'mod-2',
    module_title: 'Module 2: Modern CSS Layouts',
    progress_percentage: 33.3,
  },
  skills_summary: [
    {
      skill_id: 'skill-1',
      skill_slug: 'html-semantic-markup',
      skill_name: 'HTML5 Semantic Markup',
      discipline_slug: 'tech',
      discipline_name: 'Technology',
      mastery_level: 85.0,
      status: 'MASTERED',
      verified_attempts_count: 3,
      distinct_tasks_passed: 2,
      last_practiced_at: '2026-10-25T11:00:00Z',
      evidence: [],
      prerequisites: [],
      is_unlocked: true,
    },
  ],
  recent_attempts: [
    {
      attempt_id: 'att-1',
      activity_id: 'act-1',
      activity_title: 'Semantic HTML Quiz',
      activity_type: 'single_choice',
      score: 100,
      max_score: 100,
      passed: true,
      completed_at: '2026-10-25T11:00:00Z',
    },
  ],
  achievements: [
    {
      id: 'ach-1',
      slug: 'first_lesson',
      name: 'First Step',
      description: 'Completed your first interactive lesson.',
      icon: 'award',
      earned: true,
      earned_at: '2026-10-25T10:30:00Z',
    },
    {
      id: 'ach-2',
      slug: 'perfect_score',
      name: 'Sharpshooter',
      description: 'Achieved 100% on any assessment activity.',
      icon: 'target',
      earned: true,
      earned_at: '2026-10-25T11:00:00Z',
    },
    {
      id: 'ach-3',
      slug: 'first_course',
      name: 'Course Finisher',
      description: 'Completed your first full course version.',
      icon: 'trophy',
      earned: false,
      earned_at: null,
    },
  ],
  recommendations: [
    {
      type: 'resume',
      title: 'Continue Web Development Foundations',
      reason: 'Resume next lesson: Flexbox Alignment & Spacing',
      course_slug: 'web-dev-foundations',
      skill_slug: null,
    },
  ],
}

describe('Phase 6 — Progression and Dashboard UI Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockAuthUser = mockUser
  })

  it('renders live authenticated dashboard with active course, resume hero, and achievements', async () => {
    vi.mocked(progressApi.getDashboardSummary).mockResolvedValueOnce(sampleDashboard)

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    )

    // Verify welcome greeting with user's display name
    await waitFor(() => {
      expect(screen.getByText(/welcome back, elena rostova/i)).toBeInTheDocument()
    })

    // Verify resume learning card
    expect(screen.getAllByText(/flexbox alignment & spacing/i).length).toBeGreaterThan(0)
    expect(screen.getByRole('button', { name: /resume learning/i })).toBeInTheDocument()

    // Verify enrolled course in list
    expect(screen.getAllByText(/web development foundations/i).length).toBeGreaterThan(0)
    expect(screen.getByText(/3 of 9 lessons completed/i)).toBeInTheDocument()

    // Verify unlocked achievements
    expect(screen.getByText(/first step/i)).toBeInTheDocument()
    expect(screen.getByText(/sharpshooter/i)).toBeInTheDocument()
    expect(screen.getByText(/course finisher/i)).toBeInTheDocument()

    // Verify recommendation
    expect(screen.getByText(/continue web development foundations/i)).toBeInTheDocument()
  })

  it('renders CourseOverviewPage with Enrolled status and progress percentage for enrolled learner', async () => {
    vi.mocked(progressApi.getEnrollments).mockResolvedValueOnce([sampleEnrollment])
    const prereqResult: CoursePrerequisites = {
      course_slug: 'web-dev-foundations',
      course_title: 'Web Development Foundations',
      eligible: true,
      prerequisites: [],
    }
    vi.mocked(progressApi.checkPrerequisites).mockResolvedValueOnce(prereqResult)

    render(
      <MemoryRouter initialEntries={['/courses/web-dev-foundations']}>
        <Routes>
          <Route path="/courses/:slug" element={<CourseOverviewPage />} />
        </Routes>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getAllByText(/web development foundations/i).length).toBeGreaterThan(0)
    })

    // Verify progress bar and Continue Course button
    await waitFor(() => {
      expect(screen.getByText(/3 of 9 lessons completed/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /continue course/i })).toBeInTheDocument()
    })
  })

  it('renders prerequisite incomplete warning on CourseOverviewPage when learner is not eligible', async () => {
    vi.mocked(progressApi.getEnrollments).mockResolvedValueOnce([])
    const prereqBlocked: CoursePrerequisites = {
      course_slug: 'web-dev-foundations',
      course_title: 'Web Development Foundations',
      eligible: false,
      prerequisites: [
        {
          skill_id: 'skill-prereq-1',
          skill_slug: 'foundational-logic',
          skill_name: 'Foundational Logic',
          required_status: 'PROVISIONAL',
          current_status: 'NOT_STARTED',
          satisfied: false,
        },
      ],
    }
    vi.mocked(progressApi.checkPrerequisites).mockResolvedValueOnce(prereqBlocked)

    render(
      <MemoryRouter initialEntries={['/courses/web-dev-foundations']}>
        <Routes>
          <Route path="/courses/:slug" element={<CourseOverviewPage />} />
        </Routes>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/prerequisites incomplete/i)).toBeInTheDocument()
      expect(screen.getByText(/foundational logic/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /prerequisites required/i })).toBeDisabled()
    })
  })
})
