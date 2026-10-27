import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { CreatorStudioPage } from '../pages/CreatorStudioPage'
import { CourseEditorPage } from '../pages/CourseEditorPage'
import { LessonWorkspace } from '../features/lessons/LessonWorkspace'
import { creatorApi } from '../services/creatorApi'
import { progressApi } from '../services/progressApi'
import type { User } from '../types/auth'
import type { ApiCourseDetail } from '../types/catalog'
import type {
  CourseManagedListResponse,
  DraftValidationResponse,
  CoursePublishResponse,
} from '../types/creator'

// ── Mock Services ──────────────────────────────────────────────────────────

vi.mock('../services/creatorApi', () => ({
  creatorApi: {
    listManagedCourses: vi.fn(),
    createCourse: vi.fn(),
    deleteCourse: vi.fn(),
    getDraft: vi.fn(),
    updateMetadata: vi.fn(),
    createModule: vi.fn(),
    updateModule: vi.fn(),
    deleteModule: vi.fn(),
    createLesson: vi.fn(),
    deleteLesson: vi.fn(),
    reorderCurriculum: vi.fn(),
    updateLessonBlocks: vi.fn(),
    createActivity: vi.fn(),
    getAuthoringActivity: vi.fn(),
    updateActivity: vi.fn(),
    deleteActivity: vi.fn(),
    validateDraft: vi.fn(),
    publishCourse: vi.fn(),
    getDraftPreview: vi.fn(),
    getDraftPreviewLesson: vi.fn(),
    listDisciplines: vi.fn(),
    listSkills: vi.fn(),
  },
}))

vi.mock('../services/progressApi', () => ({
  progressApi: {
    getEnrollments: vi.fn(),
    startLesson: vi.fn(),
    completeLesson: vi.fn(),
  },
}))

// Mock Auth Context
let currentMockUser: User | null = null

vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({
    user: currentMockUser,
    loading: false,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    updateProfile: vi.fn(),
    refreshUser: vi.fn(),
  }),
  AuthProvider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}))

// ── Test Data Fixtures ─────────────────────────────────────────────────────

const mockCreatorUser: User = {
  id: 'user-creator-1',
  email: 'creator@skillverse.dev',
  role: 'creator',
  email_verified: true,
  display_name: 'Dr. Turing',
  created_at: '2026-10-20T00:00:00Z',
}

const mockLearnerUser: User = {
  id: 'user-learner-1',
  email: 'learner@skillverse.dev',
  role: 'learner',
  email_verified: true,
  display_name: 'Junior Learner',
  created_at: '2026-10-20T00:00:00Z',
}

const mockManagedCoursesResponse: CourseManagedListResponse = {
  total: 2,
  items: [
    {
      id: 'course-1',
      slug: 'intro-to-quantum',
      title: 'Introduction to Quantum Computing',
      short_description: 'Qubits, superposition, and quantum algorithms.',
      discipline_id: 'disc-physics',
      discipline_name: 'Physics & Computing',
      difficulty_level: 'INTERMEDIATE',
      estimated_duration_minutes: 180,
      status: 'DRAFT',
      creator_id: 'user-creator-1',
      published_version_number: null,
      has_draft: true,
      draft_version_id: 'ver-draft-1',
      module_count: 2,
      lesson_count: 4,
      skills: [{ id: 'sk-1', name: 'Quantum Mechanics', slug: 'quantum-mechanics' }],
      created_at: '2026-10-21T00:00:00Z',
      updated_at: '2026-10-21T00:00:00Z',
    },
    {
      id: 'course-2',
      slug: 'modern-react',
      title: 'Modern React Architecture',
      short_description: 'Deep dive into hooks, state machines, and concurrency.',
      discipline_id: 'disc-software',
      discipline_name: 'Software Engineering',
      difficulty_level: 'ADVANCED',
      estimated_duration_minutes: 240,
      status: 'PUBLISHED',
      creator_id: 'user-creator-1',
      published_version_number: 1,
      has_draft: false,
      draft_version_id: null,
      module_count: 3,
      lesson_count: 8,
      skills: [{ id: 'sk-2', name: 'React Development', slug: 'react-development' }],
      created_at: '2026-10-21T00:00:00Z',
      updated_at: '2026-10-21T00:00:00Z',
    },
  ],
}

const mockDraftCourseDetail: ApiCourseDetail = {
  id: 'course-1',
  slug: 'intro-to-quantum',
  title: 'Introduction to Quantum Computing',
  short_description: 'Qubits, superposition, and quantum algorithms.',
  full_description: 'Comprehensive overview of quantum mechanics principles.',
  discipline_id: 'disc-physics',
  difficulty_level: 'INTERMEDIATE',
  status: 'DRAFT',
  creator_id: 'user-creator-1',
  version_number: 0,
  learning_objectives: ['Understand qubits', 'Explain superposition'],
  skills: [{ id: 'sk-1', name: 'Quantum Mechanics', slug: 'quantum-mechanics', difficulty_level: 'INTERMEDIATE', sort_order: 1 }],
  modules: [
    {
      id: 'mod-1',
      title: 'Module 1: Foundations',
      description: 'Quantum state basics',
      sort_order: 1,
      lessons: [
        {
          id: 'les-1',
          slug: 'qubits-and-bloch-sphere',
          title: 'Qubits and the Bloch Sphere',
          description: 'Geometrical representation of qubit states.',
          sort_order: 1,
          content_version: 0,
          estimated_minutes: 25,
          learning_objectives: ['Visualize qubits'],
          blocks: [
            {
              id: 'b-1',
              block_type: 'heading',
              content: { text: 'The Bloch Sphere Representation', level: 2 },
              sort_order: 1,
            },
            {
              id: 'b-2',
              block_type: 'text',
              content: { text: 'A qubit state can be represented as a point on the unit sphere.' },
              sort_order: 2,
            },
          ],
          activities: [
            {
              id: 'act-1',
              lesson_id: 'les-1',
              activity_type: 'single_choice',
              title: 'Bloch Sphere Coordinates',
              instructions: 'Select the state vector corresponding to |0>.',
              configuration: {
                question: 'What is the north pole of the Bloch sphere?',
                options: [
                  { id: 'opt-0', text: '|0> state' },
                  { id: 'opt-1', text: '|1> state' },
                ],
              },
              answer_key: { correct_option_id: 'opt-0' },
              max_attempts: 3,
              passing_score: 100,
              sort_order: 1,
              is_active: true,
              created_at: '2026-10-21T00:00:00Z',
              updated_at: '2026-10-21T00:00:00Z',
            },
          ],
        },
      ],
    },
  ],
}

const mockValidationResponse: DraftValidationResponse = {
  valid: true,
  errors: [],
  warnings: [
    {
      scope: 'lesson',
      id: 'les-1',
      title: 'Qubits and the Bloch Sphere',
      message: 'Lesson duration is relatively short (25 minutes).',
    },
  ],
}

const mockPublishResponse: CoursePublishResponse = {
  course_id: 'course-1',
  version_number: 1,
  version_id: 'ver-published-1',
  publisher_id: 'user-creator-1',
  published_at: '2026-10-27T12:00:00Z',
  changelog: 'Initial publication of quantum computing foundations.',
}

// ── Test Suite ─────────────────────────────────────────────────────────────

describe('Phase 7 Creator Studio & Course Authoring', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    currentMockUser = mockCreatorUser
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // 1. Role Authorization Tests
  describe('Creator Access & Authorization', () => {
    it('prompts unauthenticated users to sign in', () => {
      currentMockUser = null

      render(
        <MemoryRouter initialEntries={['/creator']}>
          <Routes>
            <Route path="/creator" element={<CreatorStudioPage />} />
          </Routes>
        </MemoryRouter>
      )

      expect(screen.getByText(/Creator Studio/i)).toBeInTheDocument()
      expect(screen.getByText(/Please sign in to your creator account/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /Sign In to Continue/i })).toBeInTheDocument()
    })

    it('denies access to ordinary learners with explicit role explanation', () => {
      currentMockUser = mockLearnerUser

      render(
        <MemoryRouter initialEntries={['/creator']}>
          <Routes>
            <Route path="/creator" element={<CreatorStudioPage />} />
          </Routes>
        </MemoryRouter>
      )

      expect(screen.getByText(/Creator Access Required/i)).toBeInTheDocument()
      expect(screen.getByText(/learner/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /Browse Course Catalog/i })).toBeInTheDocument()
      expect(creatorApi.listManagedCourses).not.toHaveBeenCalled()
    })

    it('allows authorized creators to view managed courses and dashboard metrics', async () => {
      vi.mocked(creatorApi.listManagedCourses).mockResolvedValue(mockManagedCoursesResponse)

      render(
        <MemoryRouter initialEntries={['/creator']}>
          <Routes>
            <Route path="/creator" element={<CreatorStudioPage />} />
          </Routes>
        </MemoryRouter>
      )

      await waitFor(() => {
        expect(screen.getByText('Introduction to Quantum Computing')).toBeInTheDocument()
        expect(screen.getByText('Modern React Architecture')).toBeInTheDocument()
      })

      // Check authoring metrics
      expect(screen.getByText('Managed Courses')).toBeInTheDocument()
      expect(screen.getByText('Drafts in Authoring')).toBeInTheDocument()
      expect(screen.getByText('Published Catalog')).toBeInTheDocument()

      // Check badges
      expect(screen.getByText(/Draft \(v0\)/i)).toBeInTheDocument()
      expect(screen.getByText(/Published v1/i)).toBeInTheDocument()
    })
  })

  // 2. Search & Filter Tests
  describe('Creator Studio Filtering', () => {
    it('filters courses by title and slug using the search bar', async () => {
      vi.mocked(creatorApi.listManagedCourses).mockResolvedValue(mockManagedCoursesResponse)

      render(
        <MemoryRouter initialEntries={['/creator']}>
          <Routes>
            <Route path="/creator" element={<CreatorStudioPage />} />
          </Routes>
        </MemoryRouter>
      )

      await waitFor(() => {
        expect(screen.getByText('Introduction to Quantum Computing')).toBeInTheDocument()
      })

      const searchInput = screen.getByPlaceholderText(/Search by title or slug/i)
      fireEvent.change(searchInput, { target: { value: 'quantum' } })

      expect(screen.getByText('Introduction to Quantum Computing')).toBeInTheDocument()
      expect(screen.queryByText('Modern React Architecture')).not.toBeInTheDocument()
    })

    it('filters courses by status (Draft vs Published)', async () => {
      vi.mocked(creatorApi.listManagedCourses).mockResolvedValue(mockManagedCoursesResponse)

      render(
        <MemoryRouter initialEntries={['/creator']}>
          <Routes>
            <Route path="/creator" element={<CreatorStudioPage />} />
          </Routes>
        </MemoryRouter>
      )

      await waitFor(() => {
        expect(screen.getByText('Introduction to Quantum Computing')).toBeInTheDocument()
      })

      const draftTab = screen.getByRole('button', { name: 'Draft' })
      fireEvent.click(draftTab)

      expect(screen.getByText('Introduction to Quantum Computing')).toBeInTheDocument()
      expect(screen.queryByText('Modern React Architecture')).not.toBeInTheDocument()
    })
  })

  // 3. Course Authoring Workspace Tests
  describe('Course Authoring Workspace (CourseEditorPage)', () => {
    it('loads course draft with curriculum navigation, content blocks, and pre-publish validation', async () => {
      vi.mocked(creatorApi.getDraft).mockResolvedValue(mockDraftCourseDetail)
      vi.mocked(creatorApi.listSkills).mockResolvedValue([])
      vi.mocked(creatorApi.validateDraft).mockResolvedValue(mockValidationResponse)

      render(
        <MemoryRouter initialEntries={['/creator/courses/course-1']}>
          <Routes>
            <Route path="/creator/courses/:courseId" element={<CourseEditorPage />} />
          </Routes>
        </MemoryRouter>
      )

      await waitFor(() => {
        expect(screen.getByText('Introduction to Quantum Computing')).toBeInTheDocument()
      })

      // Verify curriculum outline loaded
      expect(screen.getByText('Module 1: Foundations')).toBeInTheDocument()
      expect(screen.getAllByText('Qubits and the Bloch Sphere').length).toBeGreaterThan(0)

      // Switch to pre-publish validation tab
      const validationTab = screen.getByRole('button', { name: /Pre-Publish Validation/i })
      fireEvent.click(validationTab)

      await waitFor(() => {
        expect(screen.getByText(/Draft is Valid for Publication/i)).toBeInTheDocument()
      })
    })

    it('allows publishing course when validation passes with changelog confirmation', async () => {
      vi.mocked(creatorApi.getDraft).mockResolvedValue(mockDraftCourseDetail)
      vi.mocked(creatorApi.listSkills).mockResolvedValue([])
      vi.mocked(creatorApi.validateDraft).mockResolvedValue(mockValidationResponse)
      vi.mocked(creatorApi.publishCourse).mockResolvedValue(mockPublishResponse)

      render(
        <MemoryRouter initialEntries={['/creator/courses/course-1']}>
          <Routes>
            <Route path="/creator/courses/:courseId" element={<CourseEditorPage />} />
          </Routes>
        </MemoryRouter>
      )

      await waitFor(() => {
        expect(screen.getByText('Introduction to Quantum Computing')).toBeInTheDocument()
      })

      // Click top Publish button
      const publishBtn = screen.getByRole('button', { name: /^Publish$/i })
      fireEvent.click(publishBtn)

      // Modal appears
      await waitFor(() => {
        expect(screen.getByText(/Publish Course Version/i)).toBeInTheDocument()
      })

      // Type changelog and confirm publication
      const changelogInput = screen.getByPlaceholderText(/Initial public release/i)
      fireEvent.change(changelogInput, { target: { value: 'First official quantum release' } })

      const confirmPublishBtn = screen.getByRole('button', { name: /Confirm & Publish/i })
      fireEvent.click(confirmPublishBtn)

      await waitFor(() => {
        expect(creatorApi.publishCourse).toHaveBeenCalledWith('course-1', 'First official quantum release')
        expect(screen.getByText(/Published Successfully/i)).toBeInTheDocument()
      })
    })
  })

  // 4. Isolated Draft Preview Tests
  describe('Draft Preview Mode in Workspace', () => {
    it('renders preview mode banner and disables learner progress mutations', async () => {
      vi.mocked(creatorApi.getDraftPreview).mockResolvedValue(mockDraftCourseDetail)
      const previewLesson = mockDraftCourseDetail.modules[0].lessons[0]
      vi.mocked(creatorApi.getDraftPreviewLesson).mockResolvedValue(previewLesson)

      render(
        <MemoryRouter initialEntries={['/creator/courses/course-1/preview/qubits-and-bloch-sphere']}>
          <Routes>
            <Route
              path="/creator/courses/:courseId/preview/:lessonSlug"
              element={<LessonWorkspace isPreview />}
            />
          </Routes>
        </MemoryRouter>
      )

      await waitFor(() => {
        expect(screen.getAllByText(/Draft Preview Mode/i).length).toBeGreaterThan(0)
        expect(screen.getByRole('button', { name: /Back to Editor/i })).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /Exit Preview/i })).toBeInTheDocument()
      })

      // Verify draft preview API was invoked rather than public course API
      expect(creatorApi.getDraftPreview).toHaveBeenCalledWith('course-1', expect.any(AbortSignal))
      expect(creatorApi.getDraftPreviewLesson).toHaveBeenCalledWith(
        'course-1',
        'qubits-and-bloch-sphere',
        expect.any(AbortSignal)
      )

      // Verify progress tracking was strictly bypassed
      expect(progressApi.startLesson).not.toHaveBeenCalled()
      expect(progressApi.getEnrollments).not.toHaveBeenCalled()

      // Verify draft content rendered in learner format
      expect(screen.getByText('The Bloch Sphere Representation')).toBeInTheDocument()
    })
  })
})
