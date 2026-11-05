import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { portfolioApi } from '../services/portfolioApi'
import { PortfolioManagementPage } from '../pages/PortfolioManagementPage'
import { PublicPortfolioPage } from '../pages/PublicPortfolioPage'
import type {
  PortfolioDetail,
  PortfolioItem,
  PortfolioPublic,
} from '../types/portfolio'
import type { SubmissionSummary } from '../types/project'
import type { User } from '../types/auth'
import { ApiError } from '../services/api'

// Mock portfolioApi
vi.mock('../services/portfolioApi', () => ({
  portfolioApi: {
    getMyPortfolio: vi.fn(),
    updateMyPortfolio: vi.fn(),
    addPortfolioItem: vi.fn(),
    updatePortfolioItem: vi.fn(),
    deletePortfolioItem: vi.fn(),
    reorderPortfolioItems: vi.fn(),
    getPublicPortfolio: vi.fn(),
    getCompletedSubmissions: vi.fn(),
  },
}))

// Mock Auth
const mockLearner: User = {
  id: 'learner-uuid-1',
  email: 'learner@skillverse.dev',
  role: 'learner',
  email_verified: true,
  created_at: '2026-10-25T00:00:00Z',
  display_name: 'Alex Rivera',
  bio: 'Software engineer and learner',
  avatar_url: null,
  timezone: 'UTC',
}

let currentAuthUser: User | null = mockLearner

vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({
    user: currentAuthUser,
    loading: false,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    updateProfile: vi.fn(),
    refreshUser: vi.fn(),
  }),
}))

describe('Phase 9 Stage 6 — Frontend Portfolio Management & Public Showcase', () => {
  const sampleItems: PortfolioItem[] = [
    {
      id: 'item-1',
      portfolio_user_id: 'learner-uuid-1',
      item_type: 'PROJECT_SUBMISSION',
      reference_id: 'sub-completed-1',
      title: 'Cloud Inventory Service API',
      summary: 'Scalable REST API with rate limiting, Alembic migrations, and JWT auth.',
      skills_demonstrated: ['FastAPI Development', 'Relational Database Design'],
      artifacts: [
        {
          id: 'art-1',
          original_filename: 'architecture_diagram.pdf',
          mime_type: 'application/pdf',
          file_size_bytes: 1024 * 500,
          download_url: '/api/v1/artifacts/art-1/download',
        },
      ],
      external_url: 'https://github.com/alex/inventory-api',
      sort_order: 0,
      visibility: 'PUBLIC',
      created_at: '2026-11-01T12:00:00Z',
      updated_at: '2026-11-01T12:00:00Z',
    },
    {
      id: 'item-2',
      portfolio_user_id: 'learner-uuid-1',
      item_type: 'CUSTOM',
      reference_id: null,
      title: 'Real-Time WebSocket Whiteboard',
      summary: 'Collaborative canvas using Canvas API and socket broadcast.',
      skills_demonstrated: ['TypeScript', 'WebSocket', 'Canvas API'],
      artifacts: [],
      external_url: 'https://whiteboard.alex.dev',
      sort_order: 1,
      visibility: 'PUBLIC',
      created_at: '2026-11-02T12:00:00Z',
      updated_at: '2026-11-02T12:00:00Z',
    },
  ]

  const samplePortfolio: PortfolioDetail = {
    user_id: 'learner-uuid-1',
    title: "Alex Rivera's Engineering Portfolio",
    headline: 'Full-Stack Developer & Distributed Systems Enthusiast',
    bio_override: 'Passionate about building responsive, accessible web applications and high-throughput backend services.',
    custom_slug: 'alex-rivera',
    visibility: 'PUBLIC',
    is_public: true,
    contact_links: {
      github: 'https://github.com/alexrivera',
      linkedin: 'https://linkedin.com/in/alexrivera',
      website: 'https://alexrivera.dev',
    },
    settings: { visibility: 'PUBLIC' },
    items: sampleItems,
    created_at: '2026-11-01T10:00:00Z',
    updated_at: '2026-11-02T10:00:00Z',
  }

  const sampleCompletedSubmissions: SubmissionSummary[] = [
    {
      id: 'sub-completed-1',
      project_id: 'proj-1',
      user_id: 'learner-uuid-1',
      version_number: 1,
      status: 'COMPLETED',
      title: 'Cloud Inventory Service API',
      score: 95.0,
      passed: true,
      created_at: '2026-11-01T10:00:00Z',
      updated_at: '2026-11-01T11:00:00Z',
    },
  ]

  beforeEach(() => {
    vi.clearAllMocks()
    currentAuthUser = mockLearner
  })

  describe('Learner Portfolio Management (/portfolio)', () => {
    it('loads and renders authenticated learner portfolio profile and items', async () => {
      vi.mocked(portfolioApi.getMyPortfolio).mockResolvedValueOnce(samplePortfolio)

      render(
        <MemoryRouter initialEntries={['/portfolio']}>
          <Routes>
            <Route path="/portfolio" element={<PortfolioManagementPage />} />
          </Routes>
        </MemoryRouter>
      )

      expect(screen.getByText(/loading your showcase portfolio/i)).toBeInTheDocument()

      await waitFor(() => {
        expect(screen.getByText(/Alex Rivera's Engineering Portfolio/i)).toBeInTheDocument()
      })

      // Items verified
      expect(screen.getByText('Cloud Inventory Service API')).toBeInTheDocument()
      expect(screen.getByText('Real-Time WebSocket Whiteboard')).toBeInTheDocument()
      expect(screen.getAllByText('FastAPI Development').length).toBeGreaterThan(0)
      expect(screen.getAllByText('Relational Database Design').length).toBeGreaterThan(0)
      expect(screen.getByText('architecture_diagram.pdf')).toBeInTheDocument()

      // Share card verified
      expect(screen.getByText('Public Showcase')).toBeInTheDocument()
      expect(screen.getByText(/\/u\/alex-rivera\/portfolio/i)).toBeInTheDocument()
    })

    it('renders empty state when learner has no portfolio items', async () => {
      const emptyPortfolio: PortfolioDetail = {
        ...samplePortfolio,
        items: [],
      }
      vi.mocked(portfolioApi.getMyPortfolio).mockResolvedValueOnce(emptyPortfolio)

      render(
        <MemoryRouter initialEntries={['/portfolio']}>
          <Routes>
            <Route path="/portfolio" element={<PortfolioManagementPage />} />
          </Routes>
        </MemoryRouter>
      )

      await waitFor(() => {
        expect(screen.getByText(/Your Showcase is Empty/i)).toBeInTheDocument()
      })

      expect(screen.getByRole('button', { name: /add your first item/i })).toBeInTheDocument()
    })

    it('switches to Profile & Links tab and saves updated metadata', async () => {
      vi.mocked(portfolioApi.getMyPortfolio).mockResolvedValueOnce(samplePortfolio)
      const updatedPortfolio: PortfolioDetail = {
        ...samplePortfolio,
        headline: 'Lead Solutions Architect',
      }
      vi.mocked(portfolioApi.updateMyPortfolio).mockResolvedValueOnce(updatedPortfolio)

      render(
        <MemoryRouter initialEntries={['/portfolio']}>
          <Routes>
            <Route path="/portfolio" element={<PortfolioManagementPage />} />
          </Routes>
        </MemoryRouter>
      )

      await waitFor(() => {
        expect(screen.getByText('Cloud Inventory Service API')).toBeInTheDocument()
      })

      // Switch to Profile & Links settings
      const settingsTab = screen.getByRole('button', { name: /profile & links/i })
      fireEvent.click(settingsTab)

      // Headline input should be visible
      const headlineInput = screen.getByLabelText(/professional headline/i)
      expect(headlineInput).toHaveValue(samplePortfolio.headline)

      fireEvent.change(headlineInput, { target: { value: 'Lead Solutions Architect' } })

      const saveBtn = screen.getByRole('button', { name: /save settings/i })
      fireEvent.click(saveBtn)

      await waitFor(() => {
        expect(portfolioApi.updateMyPortfolio).toHaveBeenCalledWith(
          expect.objectContaining({
            headline: 'Lead Solutions Architect',
          })
        )
      })

      expect(await screen.findByText(/portfolio profile updated successfully/i)).toBeInTheDocument()
    })

    it('switches visibility to UNLISTED and updates settings', async () => {
      vi.mocked(portfolioApi.getMyPortfolio).mockResolvedValueOnce(samplePortfolio)
      const unlistedPortfolio: PortfolioDetail = {
        ...samplePortfolio,
        visibility: 'UNLISTED',
        is_public: true,
      }
      vi.mocked(portfolioApi.updateMyPortfolio).mockResolvedValueOnce(unlistedPortfolio)

      render(
        <MemoryRouter initialEntries={['/portfolio']}>
          <Routes>
            <Route path="/portfolio" element={<PortfolioManagementPage />} />
          </Routes>
        </MemoryRouter>
      )

      await waitFor(() => {
        expect(screen.getByText('Cloud Inventory Service API')).toBeInTheDocument()
      })

      fireEvent.click(screen.getByRole('button', { name: /profile & links/i }))

      const unlistedRadio = screen.getByRole('radio', { name: /unlisted/i })
      fireEvent.click(unlistedRadio)

      fireEvent.click(screen.getByRole('button', { name: /save settings/i }))

      await waitFor(() => {
        expect(portfolioApi.updateMyPortfolio).toHaveBeenCalledWith(
          expect.objectContaining({
            visibility: 'UNLISTED',
          })
        )
      })
    })

    it('opens modal, fetches completed submissions, and adds capstone item', async () => {
      vi.mocked(portfolioApi.getMyPortfolio).mockResolvedValue(samplePortfolio)
      vi.mocked(portfolioApi.getCompletedSubmissions).mockResolvedValueOnce(sampleCompletedSubmissions)

      const newItem: PortfolioItem = {
        id: 'item-3',
        portfolio_user_id: 'learner-uuid-1',
        item_type: 'PROJECT_SUBMISSION',
        reference_id: 'sub-completed-1',
        title: 'Cloud Inventory Service API',
        summary: 'Completed and passed capstone project',
        skills_demonstrated: ['FastAPI Development'],
        artifacts: [],
        external_url: null,
        sort_order: 2,
        visibility: 'PUBLIC',
        created_at: '2026-11-05T00:00:00Z',
        updated_at: '2026-11-05T00:00:00Z',
      }
      vi.mocked(portfolioApi.addPortfolioItem).mockResolvedValueOnce(newItem)

      render(
        <MemoryRouter initialEntries={['/portfolio']}>
          <Routes>
            <Route path="/portfolio" element={<PortfolioManagementPage />} />
          </Routes>
        </MemoryRouter>
      )

      await waitFor(() => {
        expect(screen.getByText('Cloud Inventory Service API')).toBeInTheDocument()
      })

      const addItemBtn = screen.getByRole('button', { name: /^add item$/i })
      fireEvent.click(addItemBtn)

      // Modal appears
      await waitFor(() => {
        expect(screen.getByRole('dialog', { name: /add showcase item/i })).toBeInTheDocument()
      })

      await waitFor(() => {
        expect(portfolioApi.getCompletedSubmissions).toHaveBeenCalled()
      })

      const submitModalBtn = screen.getByRole('button', { name: /add to portfolio/i })
      fireEvent.click(submitModalBtn)

      await waitFor(() => {
        expect(portfolioApi.addPortfolioItem).toHaveBeenCalledWith(
          expect.objectContaining({
            item_type: 'PROJECT_SUBMISSION',
            reference_id: 'sub-completed-1',
            visibility: 'PUBLIC',
          })
        )
      })
    })

    it('reorders items sequentially using Move Down control', async () => {
      vi.mocked(portfolioApi.getMyPortfolio).mockResolvedValueOnce(samplePortfolio)
      const reorderedItems: PortfolioItem[] = [sampleItems[1], sampleItems[0]]
      vi.mocked(portfolioApi.reorderPortfolioItems).mockResolvedValueOnce(reorderedItems)

      render(
        <MemoryRouter initialEntries={['/portfolio']}>
          <Routes>
            <Route path="/portfolio" element={<PortfolioManagementPage />} />
          </Routes>
        </MemoryRouter>
      )

      await waitFor(() => {
        expect(screen.getByText('Cloud Inventory Service API')).toBeInTheDocument()
      })

      // First item move down button
      const moveDownBtn = screen.getByRole('button', { name: /move cloud inventory service api down/i })
      fireEvent.click(moveDownBtn)

      await waitFor(() => {
        expect(portfolioApi.reorderPortfolioItems).toHaveBeenCalledWith(['item-2', 'item-1'])
      })
    })

    it('deletes a portfolio item non-destructively upon confirmation', async () => {
      vi.mocked(portfolioApi.getMyPortfolio).mockResolvedValueOnce(samplePortfolio)
      vi.mocked(portfolioApi.deletePortfolioItem).mockResolvedValueOnce()
      vi.spyOn(window, 'confirm').mockReturnValue(true)

      render(
        <MemoryRouter initialEntries={['/portfolio']}>
          <Routes>
            <Route path="/portfolio" element={<PortfolioManagementPage />} />
          </Routes>
        </MemoryRouter>
      )

      await waitFor(() => {
        expect(screen.getByText('Cloud Inventory Service API')).toBeInTheDocument()
      })

      const deleteBtn = screen.getByRole('button', { name: /delete cloud inventory service api/i })
      fireEvent.click(deleteBtn)

      expect(window.confirm).toHaveBeenCalled()
      await waitFor(() => {
        expect(portfolioApi.deletePortfolioItem).toHaveBeenCalledWith('item-1')
      })

      expect(await screen.findByText(/item removed from portfolio/i)).toBeInTheDocument()
    })

    it('renders error state and retries fetching portfolio', async () => {
      vi.mocked(portfolioApi.getMyPortfolio)
        .mockRejectedValueOnce(new ApiError('Database connection unavailable', 'INTERNAL_ERROR', 500))
        .mockResolvedValueOnce(samplePortfolio)

      render(
        <MemoryRouter initialEntries={['/portfolio']}>
          <Routes>
            <Route path="/portfolio" element={<PortfolioManagementPage />} />
          </Routes>
        </MemoryRouter>
      )

      await waitFor(() => {
        expect(screen.getByText(/database connection unavailable/i)).toBeInTheDocument()
      })

      const retryBtn = screen.getByRole('button', { name: /retry/i })
      fireEvent.click(retryBtn)

      await waitFor(() => {
        expect(screen.getByText(/Alex Rivera's Engineering Portfolio/i)).toBeInTheDocument()
      })
    })
  })

  describe('Public Portfolio Showcase (/u/:slugOrId/portfolio)', () => {
    const publicShowcase: PortfolioPublic = {
      user_id: 'learner-uuid-1',
      display_name: 'Alex Rivera',
      avatar_url: null,
      title: "Alex Rivera's Engineering Portfolio",
      headline: 'Full-Stack Developer & Distributed Systems Enthusiast',
      bio_override: 'Passionate about building responsive, accessible web applications and high-throughput backend services.',
      custom_slug: 'alex-rivera',
      visibility: 'PUBLIC',
      contact_links: {
        github: 'https://github.com/alexrivera',
        linkedin: 'https://linkedin.com/in/alexrivera',
        website: 'https://alexrivera.dev',
      },
      settings: {},
      items: [sampleItems[0]], // Only public items
      created_at: '2026-11-01T10:00:00Z',
    }

    it('renders public portfolio showcase with headline, bio, skills, and verified artifacts', async () => {
      vi.mocked(portfolioApi.getPublicPortfolio).mockResolvedValueOnce(publicShowcase)

      render(
        <MemoryRouter initialEntries={['/u/alex-rivera/portfolio']}>
          <Routes>
            <Route path="/u/:slugOrId/portfolio" element={<PublicPortfolioPage />} />
          </Routes>
        </MemoryRouter>
      )

      expect(screen.getByText(/loading learner showcase/i)).toBeInTheDocument()

      await waitFor(() => {
        expect(screen.getByRole('heading', { level: 1, name: 'Alex Rivera' })).toBeInTheDocument()
      })

      expect(screen.getByText('Full-Stack Developer & Distributed Systems Enthusiast')).toBeInTheDocument()
      expect(screen.getByText(/passionate about building responsive/i)).toBeInTheDocument()
      expect(screen.getAllByText('FastAPI Development').length).toBeGreaterThan(0)
      expect(screen.getAllByText('Relational Database Design').length).toBeGreaterThan(0)

      // Artifact link verified
      const downloadLink = screen.getByRole('link', { name: /download architecture_diagram.pdf/i })
      expect(downloadLink).toHaveAttribute('href', '/api/v1/artifacts/art-1/download')

      // External project link verified
      const projectLink = screen.getByRole('link', { name: /view live project/i })
      expect(projectLink).toHaveAttribute('href', 'https://github.com/alex/inventory-api')
    })

    it('displays access denied message when portfolio is PRIVATE (403)', async () => {
      vi.mocked(portfolioApi.getPublicPortfolio).mockRejectedValueOnce(
        new ApiError('This portfolio is private.', 'FORBIDDEN', 403)
      )

      render(
        <MemoryRouter initialEntries={['/u/secret-user/portfolio']}>
          <Routes>
            <Route path="/u/:slugOrId/portfolio" element={<PublicPortfolioPage />} />
          </Routes>
        </MemoryRouter>
      )

      await waitFor(() => {
        expect(screen.getByText(/this portfolio is private/i)).toBeInTheDocument()
      })

      expect(
        screen.getByText(/the owner has set their portfolio visibility to private/i)
      ).toBeInTheDocument()
      expect(screen.getByRole('link', { name: /explore skillverse courses/i })).toBeInTheDocument()
    })

    it('displays 404 Not Found when portfolio does not exist', async () => {
      vi.mocked(portfolioApi.getPublicPortfolio).mockRejectedValueOnce(
        new ApiError("Portfolio 'unknown-user' was not found.", 'NOT_FOUND', 404)
      )

      render(
        <MemoryRouter initialEntries={['/u/unknown-user/portfolio']}>
          <Routes>
            <Route path="/u/:slugOrId/portfolio" element={<PublicPortfolioPage />} />
          </Routes>
        </MemoryRouter>
      )

      await waitFor(() => {
        expect(screen.getByText(/portfolio not found/i)).toBeInTheDocument()
      })

      expect(screen.getByRole('link', { name: /browse capstone projects/i })).toBeInTheDocument()
    })

    it('strictly does not expose internal storage keys or filesystem paths', async () => {
      vi.mocked(portfolioApi.getPublicPortfolio).mockResolvedValueOnce(publicShowcase)

      const { container } = render(
        <MemoryRouter initialEntries={['/u/alex-rivera/portfolio']}>
          <Routes>
            <Route path="/u/:slugOrId/portfolio" element={<PublicPortfolioPage />} />
          </Routes>
        </MemoryRouter>
      )

      await waitFor(() => {
        expect(screen.getByText('Alex Rivera')).toBeInTheDocument()
      })

      // Strict check: storage_key, filesystem paths, or private evaluator comments must not be in DOM
      expect(container.innerHTML).not.toContain('storage_key')
      expect(container.innerHTML).not.toContain('uploads/artifacts')
      expect(container.innerHTML).not.toContain('/var/data')
      expect(container.innerHTML).not.toContain('evaluator_notes')
    })
  })
})
