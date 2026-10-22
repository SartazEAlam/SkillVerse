import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { LessonWorkspace } from '../features/lessons/LessonWorkspace'
import { courseApi } from '../services/courseApi'
import type { ApiCourseDetail, ApiLessonDetail } from '../types/catalog'

// Mock the courseApi
vi.mock('../services/courseApi', () => ({
  courseApi: {
    getPublishedCourse: vi.fn(),
    getPublishedLesson: vi.fn(),
    listPublishedCourses: vi.fn(),
    getDemoCourse: vi.fn(),
  },
}))

const mockCourseDetail: ApiCourseDetail = {
  id: 'course-1',
  slug: 'python-foundations',
  title: 'Python Foundations',
  short_description: 'Master the fundamentals of Python programming.',
  full_description: 'Comprehensive Python course.',
  discipline_id: 'disc-1',
  difficulty_level: 'BEGINNER',
  status: 'PUBLISHED',
  creator_id: 'user-1',
  version_number: 1,
  published_at: '2026-10-22T10:00:00Z',
  learning_objectives: ['Learn Python basics'],
  skills: [],
  modules: [
    {
      id: 'mod-1',
      title: 'Module 1: Basics',
      description: 'Getting started',
      sort_order: 1,
      lessons: [
        {
          id: 'les-1',
          slug: 'intro-to-python',
          title: 'Introduction to Python',
          description: 'A brief history and setup of Python.',
          sort_order: 1,
          content_version: 1,
          estimated_minutes: 10,
          learning_objectives: ['Understand Python history', 'Install interpreter'],
          blocks: [],
        },
        {
          id: 'les-2',
          slug: 'variables-and-types',
          title: 'Variables and Data Types',
          description: 'Learn dynamic typing and built-in primitives.',
          sort_order: 2,
          content_version: 1,
          estimated_minutes: 15,
          learning_objectives: ['Assign variables', 'Work with numbers and strings'],
          blocks: [],
        },
      ],
    },
    {
      id: 'mod-2',
      title: 'Module 2: Flow Control',
      description: 'Conditionals and loops',
      sort_order: 2,
      lessons: [
        {
          id: 'les-3',
          slug: 'conditionals',
          title: 'Conditionals and Branching',
          description: 'if, elif, and else logic.',
          sort_order: 1,
          content_version: 1,
          estimated_minutes: 20,
          learning_objectives: ['Boolean logic', 'Write if-else chains'],
          blocks: [],
        },
      ],
    },
  ],
}

const mockLesson1Detail: ApiLessonDetail = {
  id: 'les-1',
  slug: 'intro-to-python',
  title: 'Introduction to Python',
  description: 'A brief history and setup of Python.',
  sort_order: 1,
  content_version: 1,
  estimated_minutes: 10,
  learning_objectives: ['Understand Python history', 'Install interpreter'],
  blocks: [
    {
      id: 'b-1',
      block_type: 'heading',
      content: { text: 'Welcome to Python', level: 2 },
      sort_order: 1,
    },
    {
      id: 'b-2',
      block_type: 'text',
      content: { text: 'Python is a high-level, interpreted programming language.' },
      sort_order: 2,
    },
    {
      id: 'b-3',
      block_type: 'callout',
      content: {
        title: 'Core Concept',
        message: 'Python emphasizes readable syntax and developer productivity.',
        variant: 'key_concept',
      },
      sort_order: 3,
    },
  ],
}

const mockLesson2Detail: ApiLessonDetail = {
  id: 'les-2',
  slug: 'variables-and-types',
  title: 'Variables and Data Types',
  description: 'Learn dynamic typing and built-in primitives.',
  sort_order: 2,
  content_version: 1,
  estimated_minutes: 15,
  learning_objectives: ['Assign variables', 'Work with numbers and strings'],
  blocks: [
    {
      id: 'b-2-1',
      block_type: 'heading',
      content: { text: 'Variable Assignment', level: 2 },
      sort_order: 1,
    },
    {
      id: 'b-2-2',
      block_type: 'code_example',
      content: {
        code: 'name = "SkillVerse"\ncount = 42',
        language: 'python',
        caption: 'Variables in Python',
      },
      sort_order: 2,
    },
  ],
}

describe('LessonWorkspace Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  const renderWorkspace = (route = '/learn/python-foundations/intro-to-python') => {
    return render(
      <MemoryRouter initialEntries={[route]}>
        <Routes>
          <Route path="/learn/:courseSlug/:lessonSlug" element={<LessonWorkspace />} />
          <Route path="/learn/:courseSlug" element={<LessonWorkspace />} />
          <Route path="/courses/:courseSlug" element={<div>Course Syllabus Page</div>} />
          <Route path="/explore" element={<div>Catalog Page</div>} />
        </Routes>
      </MemoryRouter>
    )
  }

  it('renders published course and lesson data from API with header, navigation, and content', async () => {
    vi.mocked(courseApi.getPublishedCourse).mockResolvedValue(mockCourseDetail)
    vi.mocked(courseApi.getPublishedLesson).mockResolvedValue(mockLesson1Detail)

    renderWorkspace('/learn/python-foundations/intro-to-python')

    // Expect loading state first
    expect(document.querySelector('.animate-pulse')).toBeInTheDocument()

    // Await loaded workspace
    await waitFor(() => {
      expect(screen.getByText('Python Foundations')).toBeInTheDocument()
      expect(screen.getByText('Published v1')).toBeInTheDocument()
    })

    // Verify header progress counter: lesson 1 of 3 (total lessons across 2 modules)
    expect(screen.getByLabelText('Lesson 1 of 3')).toBeInTheDocument()

    // Verify main content
    expect(screen.getByRole('heading', { name: 'Introduction to Python', level: 1 })).toBeInTheDocument()
    expect(screen.getByText('Understand Python history')).toBeInTheDocument()
    expect(screen.getByText('Install interpreter')).toBeInTheDocument()
    expect(screen.getByText('Welcome to Python')).toBeInTheDocument()
    expect(screen.getByText('Core Concept')).toBeInTheDocument()

    // Verify sidebar shows modules and lessons
    expect(screen.getByRole('heading', { name: 'Module 1: Basics', level: 3 })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Module 2: Flow Control', level: 3 })).toBeInTheDocument()

    // Check active lesson highlight in sidebar
    const activeLinks = screen.getAllByRole('link', { name: /Introduction to Python/i })
    const activeNavLink = activeLinks.find((l) => l.getAttribute('aria-current') === 'page')
    expect(activeNavLink).toBeDefined()
  })

  it('handles previous and next navigation controls across lesson boundaries', async () => {
    vi.mocked(courseApi.getPublishedCourse).mockResolvedValue(mockCourseDetail)
    vi.mocked(courseApi.getPublishedLesson).mockResolvedValue(mockLesson1Detail)

    renderWorkspace('/learn/python-foundations/intro-to-python')

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Introduction to Python', level: 1 })).toBeInTheDocument()
    })

    // On lesson 1: no previous lesson link; has safe return to course overview
    expect(screen.queryByText(/^Previous$/i)).toBeNull()
    const overviewLinks = screen.getAllByRole('link', { name: /Course Overview/i })
    expect(overviewLinks.length).toBeGreaterThan(0)

    // Next button should be enabled pointing to variables-and-types
    const nextBtn = screen.getByRole('link', { name: /Next Lesson/i })
    expect(nextBtn).toHaveAttribute('href', '/learn/python-foundations/variables-and-types')
  })

  it('renders intermediate lesson with both active previous and next buttons', async () => {
    vi.mocked(courseApi.getPublishedCourse).mockResolvedValue(mockCourseDetail)
    vi.mocked(courseApi.getPublishedLesson).mockResolvedValue(mockLesson2Detail)

    renderWorkspace('/learn/python-foundations/variables-and-types')

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Variables and Data Types', level: 1 })).toBeInTheDocument()
    })

    // Lesson 2 of 3 indicator
    expect(screen.getByLabelText('Lesson 2 of 3')).toBeInTheDocument()

    const prevBtn = screen.getByRole('link', { name: /Previous/i })
    expect(prevBtn).toHaveAttribute('href', '/learn/python-foundations/intro-to-python')

    const nextBtn = screen.getByRole('link', { name: /Next Lesson/i })
    expect(nextBtn).toHaveAttribute('href', '/learn/python-foundations/conditionals')
  })

  it('supports keyboard navigation via ArrowLeft and ArrowRight keys', async () => {
    vi.mocked(courseApi.getPublishedCourse).mockResolvedValue(mockCourseDetail)
    vi.mocked(courseApi.getPublishedLesson).mockResolvedValue(mockLesson1Detail)

    renderWorkspace('/learn/python-foundations/intro-to-python')

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Introduction to Python', level: 1 })).toBeInTheDocument()
    })

    // ArrowRight should trigger navigation to variables-and-types
    fireEvent.keyDown(window, { key: 'ArrowRight' })

    // Next lesson mock response
    vi.mocked(courseApi.getPublishedLesson).mockResolvedValue(mockLesson2Detail)

    await waitFor(() => {
      expect(courseApi.getPublishedLesson).toHaveBeenCalledWith(
        'python-foundations',
        'variables-and-types',
        expect.any(AbortSignal)
      )
    })
  })

  it('displays explicit Demo Track badge when rendering fallback demo course', async () => {
    const demoCourse = {
      ...mockCourseDetail,
      slug: 'demo-python',
      title: 'Demo Python',
    }
    vi.mocked(courseApi.getPublishedCourse).mockRejectedValue({
      status: 404,
      message: 'Course not found',
    })
    vi.mocked(courseApi.getDemoCourse).mockReturnValue(demoCourse)

    renderWorkspace('/learn/demo-python/intro-to-python')

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Demo Python' })).toBeInTheDocument()
      expect(screen.getByText('Demo Track')).toBeInTheDocument()
    })
  })

  it('displays error state with Retry Request button when backend API encounters an error', async () => {
    vi.mocked(courseApi.getPublishedCourse).mockRejectedValue({
      status: 500,
      message: 'Database connection failed',
    })

    renderWorkspace('/learn/python-foundations/intro-to-python')

    await waitFor(() => {
      expect(screen.getByText('Workspace Error')).toBeInTheDocument()
      expect(screen.getByText('Database connection failed')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /retry request/i })).toBeInTheDocument()
    })

    // Clicking retry calls getPublishedCourse again
    vi.mocked(courseApi.getPublishedCourse).mockResolvedValue(mockCourseDetail)
    vi.mocked(courseApi.getPublishedLesson).mockResolvedValue(mockLesson1Detail)

    fireEvent.click(screen.getByRole('button', { name: /retry request/i }))

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Introduction to Python', level: 1 })).toBeInTheDocument()
    })
  })

  it('displays not found state for nonexistent course without demo fallback', async () => {
    vi.mocked(courseApi.getPublishedCourse).mockRejectedValue({
      status: 404,
      message: 'Not found',
    })
    vi.mocked(courseApi.getDemoCourse).mockReturnValue(null)

    renderWorkspace('/learn/non-existent-course/lesson-1')

    await waitFor(() => {
      expect(screen.getByText('Lesson Not Found')).toBeInTheDocument()
      expect(screen.getByText(/Course "non-existent-course" could not be found/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /catalog/i })).toBeInTheDocument()
    })
  })

  it('displays not found state when lesson slug is not in the course outline', async () => {
    vi.mocked(courseApi.getPublishedCourse).mockResolvedValue(mockCourseDetail)

    renderWorkspace('/learn/python-foundations/unknown-lesson-slug')

    await waitFor(() => {
      expect(screen.getByText('Lesson Not Found')).toBeInTheDocument()
      expect(screen.getByText(/Lesson "unknown-lesson-slug" is not part of course/i)).toBeInTheDocument()
    })
  })

  it('toggles mobile sidebar drawer when the sidebar toggle button is clicked', async () => {
    vi.mocked(courseApi.getPublishedCourse).mockResolvedValue(mockCourseDetail)
    vi.mocked(courseApi.getPublishedLesson).mockResolvedValue(mockLesson1Detail)

    renderWorkspace('/learn/python-foundations/intro-to-python')

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Introduction to Python', level: 1 })).toBeInTheDocument()
    })

    // Mobile sidebar toggle button in header
    const toggleButton = screen.getByRole('button', { name: /open curriculum navigation/i })
    expect(toggleButton).toHaveAttribute('aria-expanded', 'false')

    fireEvent.click(toggleButton)
    expect(toggleButton).toHaveAttribute('aria-expanded', 'true')

    // Close button inside mobile drawer
    const closeButton = screen.getByRole('button', { name: /close curriculum outline/i })
    fireEvent.click(closeButton)
    expect(toggleButton).toHaveAttribute('aria-expanded', 'false')
  })

  it('handles last lesson boundary with Finish Course & Review link', async () => {
    const mockLesson3Detail: ApiLessonDetail = {
      id: 'les-3',
      slug: 'conditionals',
      title: 'Conditionals and Branching',
      description: 'if, elif, and else logic.',
      sort_order: 1,
      content_version: 1,
      estimated_minutes: 20,
      learning_objectives: ['Boolean logic'],
      blocks: [
        {
          id: 'b-3-1',
          block_type: 'heading',
          content: { text: 'Branching Summary', level: 2 },
          sort_order: 1,
        },
      ],
    }

    vi.mocked(courseApi.getPublishedCourse).mockResolvedValue(mockCourseDetail)
    vi.mocked(courseApi.getPublishedLesson).mockResolvedValue(mockLesson3Detail)

    renderWorkspace('/learn/python-foundations/conditionals')

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Conditionals and Branching', level: 1 })).toBeInTheDocument()
    })

    // On last lesson (3 of 3), Next Lesson link does NOT exist; Finish Course & Review exists
    expect(screen.queryByText(/Next Lesson/i)).toBeNull()
    const finishLink = screen.getByRole('link', { name: /Finish Course & Review/i })
    expect(finishLink).toHaveAttribute('href', '/courses/python-foundations')

    // Previous lesson button still points to lesson 2
    const prevBtn = screen.getByRole('link', { name: /Previous/i })
    expect(prevBtn).toHaveAttribute('href', '/learn/python-foundations/variables-and-types')
  })

  it('prevents loading a lesson belonging to a different course', async () => {
    vi.mocked(courseApi.getPublishedCourse).mockResolvedValue(mockCourseDetail)

    // Attempt to access a lesson from another course (e.g. vocal-resonance)
    renderWorkspace('/learn/python-foundations/vocal-resonance')

    await waitFor(() => {
      expect(screen.getByText('Lesson Not Found')).toBeInTheDocument()
      expect(
        screen.getByText(/Lesson "vocal-resonance" is not part of course "Python Foundations"/i)
      ).toBeInTheDocument()
    })

    // Confirm that getPublishedLesson is NOT called for foreign lesson
    expect(courseApi.getPublishedLesson).not.toHaveBeenCalledWith(
      'python-foundations',
      'vocal-resonance',
      expect.any(AbortSignal)
    )
  })
})
