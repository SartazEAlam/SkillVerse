import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { projectApi } from '../services/projectApi'
import { ProjectsPage } from '../pages/ProjectsPage'
import { ProjectDetailPage } from '../pages/ProjectDetailPage'
import { SubmissionWorkspacePage } from '../pages/SubmissionWorkspacePage'
import type {
  Artifact,
  ProjectDetail,
  ProjectPaginatedResponse,
  ProjectSummary,
  SubmissionDetail,
  SubmissionHistoryResponse,
} from '../types/project'
import type { ApiDiscipline } from '../types/catalog'
import type { User } from '../types/auth'

// Mock projectApi
vi.mock('../services/projectApi', () => ({
  projectApi: {
    listProjects: vi.fn(),
    getProject: vi.fn(),
    startOrGetSubmission: vi.fn(),
    getMySubmissions: vi.fn(),
    getSubmission: vi.fn(),
    updateDraftSubmission: vi.fn(),
    submitProject: vi.fn(),
    createRevision: vi.fn(),
    getSubmissionHistory: vi.fn(),
    listSubmissionArtifacts: vi.fn(),
    uploadArtifact: vi.fn(),
    deleteArtifact: vi.fn(),
    listDisciplines: vi.fn(),
    listSkills: vi.fn(),
  },
}))

// Mock Auth
const mockLearner: User = {
  id: 'user-learner-1',
  email: 'learner@skillverse.dev',
  role: 'learner',
  email_verified: true,
  created_at: '2026-10-25T00:00:00Z',
  display_name: 'Alex Rivera',
  bio: 'Software engineer and learner',
  avatar_url: null,
  timezone: 'UTC',
}

let mockAuthUser: User | null = mockLearner

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

// Test Fixtures
const sampleDiscipline: ApiDiscipline = {
  id: 'disc-tech',
  slug: 'technology',
  name: 'Technology & Software',
  description: 'Software development, cloud architecture, and systems engineering',
  icon: 'code',
  sort_order: 1,
  is_active: true,
  created_at: '2026-10-01T00:00:00Z',
  skills_count: 5,
}

const sampleProjectSummary: ProjectSummary = {
  id: 'proj-1',
  slug: 'cloud-inventory-api',
  title: 'Cloud Inventory Microservice',
  short_description: 'Build a production-ready inventory REST API with schema validation, rate limiting, and database migrations.',
  discipline_id: 'disc-tech',
  discipline_name: 'Technology & Software',
  discipline_slug: 'technology',
  difficulty_level: 'INTERMEDIATE',
  estimated_duration_hours: 15,
  status: 'PUBLISHED',
  creator_id: 'user-creator-1',
  created_at: '2026-11-01T00:00:00Z',
  updated_at: '2026-11-01T00:00:00Z',
  skills: [
    {
      skill_id: 'skill-api',
      skill_slug: 'api-architecture',
      skill_name: 'API Architecture',
      difficulty_level: 'INTERMEDIATE',
      is_primary: true,
    },
    {
      skill_id: 'skill-db',
      skill_slug: 'relational-db',
      skill_name: 'Database Design',
      difficulty_level: 'ADVANCED',
      is_primary: false,
    },
  ],
  submissions_count: 8,
}

const sampleProjectDetail: ProjectDetail = {
  ...sampleProjectSummary,
  full_description: 'Detailed project specification requiring SQLite/PostgreSQL schema modeling, Alembic migrations, CRUD routes, and security testing.',
  course_version_id: 'cv-1',
  requirements: {
    milestones: [
      { id: 'm1', title: 'Database Schema Modeling', description: 'Create normalized relational schema' },
      { id: 'm2', title: 'REST Endpoints Implementation', description: 'Build and validate CRUD routes' },
    ],
    deliverables: [
      { id: 'd1', title: 'GitHub Repository URL', description: 'Link to public or private source code repository' },
      { id: 'd2', title: 'Design Documentation PDF', description: 'Architecture diagram and schema documentation' },
    ],
    guidelines: ['Code must include automated tests', 'Follow RESTful HTTP conventions'],
    artifact_limits: { max_files: 10, max_file_size_mb: 20 },
  },
  evaluation_criteria: {
    passing_score: 75.0,
    rubric: [
      { id: 'c1', title: 'Schema Architecture & Migration', max_score: 50.0, weight: 1.0, description: 'Sound relational design and migration safety' },
      { id: 'c2', title: 'API Correctness & Error Handling', max_score: 50.0, weight: 1.0, description: 'Status codes, validation schemas, and rate limits' },
    ],
  },
  starter_resources: [
    { title: 'Inventory Starter Boilerplate', url: 'https://github.com/skillverse/inventory-starter', description: 'Template structure and tests' },
  ],
  creator_name: 'Dr. Sarah Connor',
  my_submission: null,
}

const sampleArtifact: Artifact = {
  id: 'art-1',
  submission_id: 'sub-1',
  user_id: 'user-learner-1',
  storage_key: 'submissions/sub-1/report_abc123.pdf',
  original_filename: 'architecture_report.pdf',
  mime_type: 'application/pdf',
  file_size_bytes: 1024 * 512, // 512 KB
  checksum_sha256: 'a1b2c3d4e5f6',
  is_public: true,
  created_at: '2026-11-02T10:00:00Z',
  download_url: '/api/v1/artifacts/art-1/download',
}

const sampleDraftSubmission: SubmissionDetail = {
  id: 'sub-1',
  project_id: 'proj-1',
  user_id: 'user-learner-1',
  version_number: 1,
  revision_of_id: null,
  status: 'DRAFT',
  title: 'My Inventory API Attempt',
  summary: 'Implemented FastAPI routes with SQLAlchemy models and migration scripts.',
  content: {
    repo_url: 'https://github.com/alex/inventory-api',
    demo_url: 'https://inventory-demo.dev',
    notes: 'Ran tests with pytest',
  },
  milestones_completed: ['m1'],
  evaluation: null,
  evaluator_id: null,
  evaluator_name: null,
  artifacts: [sampleArtifact],
  revisions_count: 0,
  score: null,
  passed: null,
  submitted_at: null,
  evaluated_at: null,
  created_at: '2026-11-02T09:00:00Z',
  updated_at: '2026-11-02T10:00:00Z',
  transition_history: [
    { from_status: null, to_status: 'DRAFT', timestamp: '2026-11-02T09:00:00Z', reason: 'Draft started' },
  ],
}

describe('Phase 9 Stage 5 — Frontend Projects & Submissions UI', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockAuthUser = mockLearner
    ;(projectApi.listDisciplines as any).mockResolvedValue([sampleDiscipline])
  })

  // ───────────────────────────────────────────────────────────────────────────
  // 1. Projects Discovery Page
  // ───────────────────────────────────────────────────────────────────────────
  describe('Project Discovery & Catalog (/projects)', () => {
    it('renders published projects catalog with title, skills, difficulty, and duration', async () => {
      const mockResponse: ProjectPaginatedResponse = {
        items: [sampleProjectSummary],
        total: 1,
        page: 1,
        limit: 12,
        pages: 1,
      }
      ;(projectApi.listProjects as any).mockResolvedValue(mockResponse)

      render(
        <MemoryRouter initialEntries={['/projects']}>
          <Routes>
            <Route path="/projects" element={<ProjectsPage />} />
          </Routes>
        </MemoryRouter>
      )

      // Loading state initially
      expect(screen.getByLabelText(/loading projects/i)).toBeInTheDocument()

      // Projects loaded
      await waitFor(() => {
        expect(screen.getByText('Cloud Inventory Microservice')).toBeInTheDocument()
      })

      expect(screen.getByText(/build a production-ready inventory rest api/i)).toBeInTheDocument()
      expect(screen.getAllByText('Intermediate').length).toBeGreaterThanOrEqual(1)
      expect(screen.getByText('15h est.')).toBeInTheDocument()
      expect(screen.getByText('API Architecture')).toBeInTheDocument()
      expect(screen.getAllByText('Technology & Software').length).toBeGreaterThanOrEqual(1)
      expect(screen.getByText('8 submissions')).toBeInTheDocument()
      expect(screen.getByLabelText(/view details for cloud inventory microservice/i)).toBeInTheDocument()
    })

    it('filters projects by search keyword', async () => {
      const mockResponse: ProjectPaginatedResponse = {
        items: [sampleProjectSummary],
        total: 1,
        page: 1,
        limit: 12,
        pages: 1,
      }
      ;(projectApi.listProjects as any).mockResolvedValue(mockResponse)

      render(
        <MemoryRouter initialEntries={['/projects']}>
          <Routes>
            <Route path="/projects" element={<ProjectsPage />} />
          </Routes>
        </MemoryRouter>
      )

      await waitFor(() => {
        expect(screen.getByText('Cloud Inventory Microservice')).toBeInTheDocument()
      })

      const searchInput = screen.getByLabelText(/search projects by title or description/i)
      fireEvent.change(searchInput, { target: { value: 'inventory' } })

      await waitFor(() => {
        expect(projectApi.listProjects).toHaveBeenCalledWith(
          expect.objectContaining({ search: 'inventory', page: 1 })
        )
      })
      await waitFor(() => {
        expect(screen.getByText('Cloud Inventory Microservice')).toBeInTheDocument()
      })
    })

    it('renders empty state when no projects match filters and allows resetting filters', async () => {
      const emptyResponse: ProjectPaginatedResponse = {
        items: [],
        total: 0,
        page: 1,
        limit: 12,
        pages: 0,
      }
      ;(projectApi.listProjects as any).mockResolvedValue(emptyResponse)

      render(
        <MemoryRouter initialEntries={['/projects']}>
          <Routes>
            <Route path="/projects" element={<ProjectsPage />} />
          </Routes>
        </MemoryRouter>
      )

      await waitFor(() => {
        expect(screen.getByText(/no matching projects found/i)).toBeInTheDocument()
      })

      const resetBtn = screen.getByRole('button', { name: /reset all filters/i })
      fireEvent.click(resetBtn)

      await waitFor(() => {
        expect(projectApi.listProjects).toHaveBeenCalledWith(
          expect.objectContaining({ page: 1, sort_by: 'created_at', sort_order: 'desc' })
        )
      })
      await waitFor(() => {
        expect(screen.getByText(/no matching projects found/i)).toBeInTheDocument()
      })
    })

    it('renders error state with retry button on network failure', async () => {
      ;(projectApi.listProjects as any).mockRejectedValueOnce(new Error('Database gateway timeout'))

      render(
        <MemoryRouter initialEntries={['/projects']}>
          <Routes>
            <Route path="/projects" element={<ProjectsPage />} />
          </Routes>
        </MemoryRouter>
      )

      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument()
        expect(screen.getByText(/database gateway timeout/i)).toBeInTheDocument()
      })

      const retryBtn = screen.getByRole('button', { name: /retry connection/i })
      expect(retryBtn).toBeInTheDocument()

      ;(projectApi.listProjects as any).mockResolvedValue({
        items: [sampleProjectSummary],
        total: 1,
        page: 1,
        limit: 12,
        pages: 1,
      })

      fireEvent.click(retryBtn)

      await waitFor(() => {
        expect(screen.getByText('Cloud Inventory Microservice')).toBeInTheDocument()
      })
    })
  })

  // ───────────────────────────────────────────────────────────────────────────
  // 2. Project Details Page
  // ───────────────────────────────────────────────────────────────────────────
  describe('Project Details & Rubric Specification (/projects/:slugOrId)', () => {
    it('renders full project description, milestones, deliverables, and rubric breakdown', async () => {
      ;(projectApi.getProject as any).mockResolvedValue(sampleProjectDetail)

      render(
        <MemoryRouter initialEntries={['/projects/cloud-inventory-api']}>
          <Routes>
            <Route path="/projects/:slugOrId" element={<ProjectDetailPage />} />
          </Routes>
        </MemoryRouter>
      )

      await waitFor(() => {
        expect(screen.getByRole('heading', { level: 1, name: 'Cloud Inventory Microservice' })).toBeInTheDocument()
      })

      // Milestones
      expect(screen.getByText(/database schema modeling/i)).toBeInTheDocument()
      expect(screen.getByText(/rest endpoints implementation/i)).toBeInTheDocument()

      // Deliverables
      expect(screen.getByText(/github repository url/i)).toBeInTheDocument()
      expect(screen.getByText(/design documentation pdf/i)).toBeInTheDocument()

      // Rubric
      expect(screen.getByText(/passing standard/i)).toBeInTheDocument()
      expect(screen.getByText('75%')).toBeInTheDocument()
      expect(screen.getByText('Schema Architecture & Migration')).toBeInTheDocument()
      expect(screen.getAllByText('Max: 50 pts').length).toBe(2)

      // Integrity Protection notice
      expect(screen.getByText(/integrity protection:/i)).toBeInTheDocument()

      // Starter template link
      expect(screen.getByText('Inventory Starter Boilerplate')).toBeInTheDocument()
    })

    it('allows authenticated learner to start project and redirects to workspace', async () => {
      ;(projectApi.getProject as any).mockResolvedValue(sampleProjectDetail)
      ;(projectApi.startOrGetSubmission as any).mockResolvedValue(sampleDraftSubmission)

      render(
        <MemoryRouter initialEntries={['/projects/cloud-inventory-api']}>
          <Routes>
            <Route path="/projects/:slugOrId" element={<ProjectDetailPage />} />
            <Route path="/submissions/:submissionId" element={<div data-testid="workspace-view">Workspace Page</div>} />
          </Routes>
        </MemoryRouter>
      )

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /start project/i })).toBeInTheDocument()
      })

      const startBtn = screen.getByRole('button', { name: /start project/i })
      fireEvent.click(startBtn)

      await waitFor(() => {
        expect(projectApi.startOrGetSubmission).toHaveBeenCalledWith('proj-1')
        expect(screen.getByTestId('workspace-view')).toBeInTheDocument()
      })
    })

    it('redirects unauthenticated user to login with return redirect query parameter', async () => {
      mockAuthUser = null // Logged out
      ;(projectApi.getProject as any).mockResolvedValue(sampleProjectDetail)

      render(
        <MemoryRouter initialEntries={['/projects/cloud-inventory-api']}>
          <Routes>
            <Route path="/projects/:slugOrId" element={<ProjectDetailPage />} />
            <Route path="/login" element={<div data-testid="login-redirect">Login Screen</div>} />
          </Routes>
        </MemoryRouter>
      )

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /start project/i })).toBeInTheDocument()
      })

      const startBtn = screen.getByRole('button', { name: /start project/i })
      fireEvent.click(startBtn)

      await waitFor(() => {
        expect(screen.getByTestId('login-redirect')).toBeInTheDocument()
      })
    })
  })

  // ───────────────────────────────────────────────────────────────────────────
  // 3. Submission Workspace Page & Artifact Handling
  // ───────────────────────────────────────────────────────────────────────────
  describe('Submission Workspace, Artifact Uploads & Lifecycle (/submissions/:submissionId)', () => {
    it('renders draft submission workspace with editable fields, milestone toggles, and artifacts', async () => {
      ;(projectApi.getSubmission as any).mockResolvedValue(sampleDraftSubmission)
      ;(projectApi.getProject as any).mockResolvedValue(sampleProjectDetail)
      ;(projectApi.getSubmissionHistory as any).mockResolvedValue({
        project_id: 'proj-1',
        user_id: 'user-learner-1',
        current_version: 1,
        submissions: [sampleDraftSubmission],
      })

      render(
        <MemoryRouter initialEntries={['/submissions/sub-1']}>
          <Routes>
            <Route path="/submissions/:submissionId" element={<SubmissionWorkspacePage />} />
          </Routes>
        </MemoryRouter>
      )

      await waitFor(() => {
        expect(screen.getByText('Cloud Inventory Microservice')).toBeInTheDocument()
      })

      expect(screen.getByText('Draft In Progress')).toBeInTheDocument()
      expect(screen.getByText('Version 1')).toBeInTheDocument()

      // Draft inputs
      const titleInput = screen.getByLabelText(/submission title/i) as HTMLInputElement
      expect(titleInput.value).toBe('My Inventory API Attempt')

      const summaryInput = screen.getByLabelText(/summary & approach notes/i) as HTMLTextAreaElement
      expect(summaryInput.value).toContain('Implemented FastAPI routes')

      // Milestones checklist: m1 is completed
      const m1Checkbox = screen.getByLabelText(/mark milestone database schema modeling as incomplete/i) as HTMLInputElement
      expect(m1Checkbox.checked).toBe(true)

      // Artifacts list
      expect(screen.getByText('architecture_report.pdf')).toBeInTheDocument()
      expect(screen.getByText('Showcase')).toBeInTheDocument()
    })

    it('saves draft progress and milestone updates without submitting', async () => {
      ;(projectApi.getSubmission as any).mockResolvedValue(sampleDraftSubmission)
      ;(projectApi.getProject as any).mockResolvedValue(sampleProjectDetail)
      ;(projectApi.updateDraftSubmission as any).mockResolvedValue({
        ...sampleDraftSubmission,
        summary: 'Updated summary notes for rubric review.',
        milestones_completed: ['m1', 'm2'],
      })

      render(
        <MemoryRouter initialEntries={['/submissions/sub-1']}>
          <Routes>
            <Route path="/submissions/:submissionId" element={<SubmissionWorkspacePage />} />
          </Routes>
        </MemoryRouter>
      )

      await waitFor(() => {
        expect(screen.getByText('Save Draft')).toBeInTheDocument()
      })

      const summaryInput = screen.getByLabelText(/summary & approach notes/i)
      fireEvent.change(summaryInput, { target: { value: 'Updated summary notes for rubric review.' } })

      // Toggle m2
      const m2Checkbox = screen.getByLabelText(/mark milestone rest endpoints implementation as completed/i)
      fireEvent.click(m2Checkbox)

      const saveBtn = screen.getByRole('button', { name: /save draft/i })
      fireEvent.click(saveBtn)

      await waitFor(() => {
        expect(projectApi.updateDraftSubmission).toHaveBeenCalledWith(
          'sub-1',
          expect.objectContaining({
            summary: 'Updated summary notes for rubric review.',
            milestones_completed: ['m1', 'm2'],
          })
        )
      })

      expect(screen.getByText(/draft progress successfully saved/i)).toBeInTheDocument()
    })

    it('rejects dangerous script file types client-side without calling API', async () => {
      ;(projectApi.getSubmission as any).mockResolvedValue(sampleDraftSubmission)
      ;(projectApi.getProject as any).mockResolvedValue(sampleProjectDetail)

      render(
        <MemoryRouter initialEntries={['/submissions/sub-1']}>
          <Routes>
            <Route path="/submissions/:submissionId" element={<SubmissionWorkspacePage />} />
          </Routes>
        </MemoryRouter>
      )

      await waitFor(() => {
        expect(screen.getByLabelText(/upload deliverable file/i)).toBeInTheDocument()
      })

      const fileInput = screen.getByLabelText(/upload deliverable file/i) as HTMLInputElement
      const maliciousScript = new File(['import os; os.system("rm -rf")'], 'exploit.py', {
        type: 'text/x-python',
      })

      fireEvent.change(fileInput, { target: { files: [maliciousScript] } })

      // Should display instant validation error
      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument()
        expect(screen.getByText(/files with extension "\.py" are restricted for security reasons/i)).toBeInTheDocument()
      })

      // Must never call upload API
      expect(projectApi.uploadArtifact).not.toHaveBeenCalled()
    })

    it('rejects files exceeding 20MB client-side', async () => {
      ;(projectApi.getSubmission as any).mockResolvedValue(sampleDraftSubmission)
      ;(projectApi.getProject as any).mockResolvedValue(sampleProjectDetail)

      render(
        <MemoryRouter initialEntries={['/submissions/sub-1']}>
          <Routes>
            <Route path="/submissions/:submissionId" element={<SubmissionWorkspacePage />} />
          </Routes>
        </MemoryRouter>
      )

      await waitFor(() => {
        expect(screen.getByLabelText(/upload deliverable file/i)).toBeInTheDocument()
      })

      const fileInput = screen.getByLabelText(/upload deliverable file/i) as HTMLInputElement
      const oversizedFile = new File(['large_data'], 'giant_archive.zip', {
        type: 'application/zip',
      })
      Object.defineProperty(oversizedFile, 'size', { value: 25 * 1024 * 1024 }) // 25 MB

      fireEvent.change(fileInput, { target: { files: [oversizedFile] } })

      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument()
        expect(screen.getByText(/exceeds the individual limit of 20 mb/i)).toBeInTheDocument()
      })

      expect(projectApi.uploadArtifact).not.toHaveBeenCalled()
    })

    it('uploads valid artifact file and updates artifact list', async () => {
      ;(projectApi.getSubmission as any).mockResolvedValue(sampleDraftSubmission)
      ;(projectApi.getProject as any).mockResolvedValue(sampleProjectDetail)

      const uploadedZip: Artifact = {
        id: 'art-2',
        submission_id: 'sub-1',
        user_id: 'user-learner-1',
        storage_key: 'submissions/sub-1/source_bundle.zip',
        original_filename: 'source_bundle.zip',
        mime_type: 'application/zip',
        file_size_bytes: 1024 * 1024 * 2, // 2MB
        checksum_sha256: 'f1e2d3c4b5a6',
        is_public: false,
        created_at: '2026-11-02T11:00:00Z',
        download_url: '/api/v1/artifacts/art-2/download',
      }
      ;(projectApi.uploadArtifact as any).mockResolvedValue(uploadedZip)

      render(
        <MemoryRouter initialEntries={['/submissions/sub-1']}>
          <Routes>
            <Route path="/submissions/:submissionId" element={<SubmissionWorkspacePage />} />
          </Routes>
        </MemoryRouter>
      )

      await waitFor(() => {
        expect(screen.getByLabelText(/upload deliverable file/i)).toBeInTheDocument()
      })

      const fileInput = screen.getByLabelText(/upload deliverable file/i) as HTMLInputElement
      const validZip = new File(['PKzipcontent'], 'source_bundle.zip', {
        type: 'application/zip',
      })

      fireEvent.change(fileInput, { target: { files: [validZip] } })

      await waitFor(() => {
        expect(projectApi.uploadArtifact).toHaveBeenCalledWith('sub-1', validZip, false)
        expect(screen.getByText('source_bundle.zip')).toBeInTheDocument()
      })
    })

    it('submits deliverables and updates submission status to SUBMITTED', async () => {
      ;(projectApi.getSubmission as any).mockResolvedValue(sampleDraftSubmission)
      ;(projectApi.getProject as any).mockResolvedValue(sampleProjectDetail)
      ;(projectApi.updateDraftSubmission as any).mockResolvedValue(sampleDraftSubmission)

      const submittedSub: SubmissionDetail = {
        ...sampleDraftSubmission,
        status: 'SUBMITTED',
        submitted_at: '2026-11-02T12:00:00Z',
      }
      ;(projectApi.submitProject as any).mockResolvedValue(submittedSub)

      render(
        <MemoryRouter initialEntries={['/submissions/sub-1']}>
          <Routes>
            <Route path="/submissions/:submissionId" element={<SubmissionWorkspacePage />} />
          </Routes>
        </MemoryRouter>
      )

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /submit for evaluation/i })).toBeInTheDocument()
      })

      const submitBtn = screen.getByRole('button', { name: /submit for evaluation/i })
      fireEvent.click(submitBtn)

      await waitFor(() => {
        expect(projectApi.submitProject).toHaveBeenCalledWith('sub-1')
        expect(screen.getByText('Submitted for Evaluation')).toBeInTheDocument()
      })

      // Draft action buttons must now be disabled/hidden
      expect(screen.queryByRole('button', { name: /save draft/i })).not.toBeInTheDocument()
    })
  })

  // ───────────────────────────────────────────────────────────────────────────
  // 4. Evaluation Feedback & Revision Workflow
  // ───────────────────────────────────────────────────────────────────────────
  describe('Evaluation Feedback & Revision Workflow', () => {
    it('displays evaluator feedback, criteria breakdown, and revision launch when changes requested', async () => {
      const changesRequestedSub: SubmissionDetail = {
        ...sampleDraftSubmission,
        status: 'CHANGES_REQUESTED',
        score: 65.0,
        passed: false,
        evaluated_at: '2026-11-02T14:00:00Z',
        evaluator_name: 'Dr. Sarah Connor',
        evaluation: {
          passing_score: 75.0,
          score: 65.0,
          passed: false,
          feedback: 'Solid API architecture, but please add rate limiting middleware to prevent brute force on auth endpoints.',
          criteria_scores: [
            { criterion_id: 'c1', score: 45.0, feedback: 'Clean database schema design.' },
            { criterion_id: 'c2', score: 20.0, feedback: 'Missing rate limit protection.' },
          ],
        },
      }

      ;(projectApi.getSubmission as any).mockResolvedValue(changesRequestedSub)
      ;(projectApi.getProject as any).mockResolvedValue(sampleProjectDetail)
      ;(projectApi.getSubmissionHistory as any).mockResolvedValue({
        project_id: 'proj-1',
        user_id: 'user-learner-1',
        current_version: 1,
        submissions: [changesRequestedSub],
      })

      render(
        <MemoryRouter initialEntries={['/submissions/sub-1']}>
          <Routes>
            <Route path="/submissions/:submissionId" element={<SubmissionWorkspacePage />} />
          </Routes>
        </MemoryRouter>
      )

      await waitFor(() => {
        expect(screen.getByText('Revision & Changes Requested')).toBeInTheDocument()
      })

      // Score and targets
      expect(screen.getByText('65.0')).toBeInTheDocument()
      expect(screen.getAllByText('75%').length).toBeGreaterThanOrEqual(1)

      // Evaluator written remarks
      expect(screen.getByText(/please add rate limiting middleware/i)).toBeInTheDocument()
      expect(screen.getByText(/evaluated by/i)).toBeInTheDocument()
      expect(screen.getByText('Dr. Sarah Connor')).toBeInTheDocument()

      // Criteria scores
      expect(screen.getByText('45 / 50 pts')).toBeInTheDocument()
      expect(screen.getByText('20 / 50 pts')).toBeInTheDocument()

      // "Start Revision Draft" button is visible
      expect(screen.getByRole('button', { name: /start revision draft/i })).toBeInTheDocument()
    })

    it('launches new revision draft upon clicking Start Revision Draft and navigates to new submission', async () => {
      const changesRequestedSub: SubmissionDetail = {
        ...sampleDraftSubmission,
        status: 'CHANGES_REQUESTED',
        score: 65.0,
        passed: false,
        evaluation: {
          passing_score: 75.0,
          score: 65.0,
          passed: false,
          feedback: 'Please revise rate limiting.',
        },
      }

      const revisionSub: SubmissionDetail = {
        ...sampleDraftSubmission,
        id: 'sub-2',
        version_number: 2,
        revision_of_id: 'sub-1',
        status: 'DRAFT',
        title: 'My Inventory API Attempt (Rev 2)',
        score: null,
        passed: null,
        evaluation: null,
      }

      ;(projectApi.getSubmission as any).mockResolvedValue(changesRequestedSub)
      ;(projectApi.getProject as any).mockResolvedValue(sampleProjectDetail)
      ;(projectApi.createRevision as any).mockResolvedValue(revisionSub)

      render(
        <MemoryRouter initialEntries={['/submissions/sub-1']}>
          <Routes>
            <Route path="/submissions/:submissionId" element={<SubmissionWorkspacePage />} />
            <Route path="/submissions/sub-2" element={<div data-testid="revision-workspace">Revision v2 Workspace</div>} />
          </Routes>
        </MemoryRouter>
      )

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /start revision draft/i })).toBeInTheDocument()
      })

      const revBtn = screen.getByRole('button', { name: /start revision draft/i })
      fireEvent.click(revBtn)

      await waitFor(() => {
        expect(projectApi.createRevision).toHaveBeenCalledWith('sub-1')
        expect(screen.getByTestId('revision-workspace')).toBeInTheDocument()
      })
    })

    it('displays revision history timeline showing multiple versions and status badges', async () => {
      const historyResponse: SubmissionHistoryResponse = {
        project_id: 'proj-1',
        user_id: 'user-learner-1',
        current_version: 2,
        submissions: [
          {
            id: 'sub-1',
            project_id: 'proj-1',
            user_id: 'user-learner-1',
            version_number: 1,
            status: 'CHANGES_REQUESTED',
            score: 65.0,
            passed: false,
            created_at: '2026-11-01T09:00:00Z',
            updated_at: '2026-11-01T14:00:00Z',
          },
          {
            id: 'sub-2',
            project_id: 'proj-1',
            user_id: 'user-learner-1',
            version_number: 2,
            status: 'COMPLETED',
            score: 92.0,
            passed: true,
            created_at: '2026-11-02T09:00:00Z',
            updated_at: '2026-11-02T16:00:00Z',
          },
        ],
      }

      const completedSub: SubmissionDetail = {
        ...sampleDraftSubmission,
        id: 'sub-2',
        version_number: 2,
        status: 'COMPLETED',
        score: 92.0,
        passed: true,
        evaluation: {
          passing_score: 75.0,
          score: 92.0,
          passed: true,
          feedback: 'Excellent rate limiting implementation with leaky bucket algorithm.',
        },
      }

      ;(projectApi.getSubmission as any).mockResolvedValue(completedSub)
      ;(projectApi.getProject as any).mockResolvedValue(sampleProjectDetail)
      ;(projectApi.getSubmissionHistory as any).mockResolvedValue(historyResponse)

      render(
        <MemoryRouter initialEntries={['/submissions/sub-2']}>
          <Routes>
            <Route path="/submissions/:submissionId" element={<SubmissionWorkspacePage />} />
          </Routes>
        </MemoryRouter>
      )

      await waitFor(() => {
        expect(screen.getByText('Passed & Completed')).toBeInTheDocument()
      })

      // Revision history section
      expect(screen.getByText(/revision history & versions/i)).toBeInTheDocument()
      expect(screen.getByText('Version 1')).toBeInTheDocument()
      expect(screen.getAllByText('Version 2').length).toBeGreaterThanOrEqual(1)
      expect(screen.getByText('Active Workspace')).toBeInTheDocument()
      expect(screen.getByText(/score: 65\.0\/100/i)).toBeInTheDocument()
      expect(screen.getByRole('link', { name: /inspect/i })).toBeInTheDocument()
    })
  })
})
