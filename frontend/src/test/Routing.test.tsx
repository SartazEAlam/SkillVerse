import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { Shell } from '../components/layout/Shell'
import { DashboardPage } from '../pages/DashboardPage'
import { ExplorePage } from '../pages/ExplorePage'
import { SkillsPage } from '../pages/SkillsPage'
import { CourseOverviewPage } from '../pages/CourseOverviewPage'
import { CreatorStudioPage } from '../pages/CreatorStudioPage'
import { NotFoundPage } from '../pages/NotFoundPage'

describe('Application Routing & Navigation', () => {
  const renderWithRoute = (initialPath: string) => {
    return render(
      <MemoryRouter initialEntries={[initialPath]}>
        <Routes>
          <Route path="/" element={<Shell />}>
            <Route index element={<DashboardPage />} />
            <Route path="explore" element={<ExplorePage />} />
            <Route path="skills" element={<SkillsPage />} />
            <Route path="creator" element={<CreatorStudioPage />} />
            <Route path="courses/:slug" element={<CourseOverviewPage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Route>
        </Routes>
      </MemoryRouter>
    )
  }

  it('renders DashboardPage at root path /', () => {
    renderWithRoute('/')
    expect(screen.getByText(/welcome back, alex morgan/i)).toBeInTheDocument()
    expect(screen.getByText(/the skillverse approach/i)).toBeInTheDocument()
  })

  it('renders ExplorePage at /explore', () => {
    renderWithRoute('/explore')
    expect(screen.getByRole('heading', { name: /explore interactive courses/i })).toBeInTheDocument()
  })

  it('renders SkillsPage at /skills with visual and list toggles', () => {
    renderWithRoute('/skills')
    expect(screen.getByRole('heading', { name: /cross-disciplinary skill map/i })).toBeInTheDocument()

    // Switch to accessible list view
    const listBtn = screen.getByRole('button', { name: /accessible list/i })
    fireEvent.click(listBtn)
    expect(screen.getByText(/accessible structured tree/i)).toBeInTheDocument()
  })

  it('renders CourseOverviewPage at valid course slug /courses/web-dev-foundations', () => {
    renderWithRoute('/courses/web-dev-foundations')
    expect(screen.getByRole('heading', { name: /web development foundations/i })).toBeInTheDocument()
    expect(screen.getByText(/chapter 1/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /start course preview/i })).toBeInTheDocument()
  })

  it('renders course not found for invalid slug /courses/non-existent-slug', () => {
    renderWithRoute('/courses/non-existent-slug')
    expect(screen.getByText(/course not found/i)).toBeInTheDocument()
  })

  it('renders 404 NotFoundPage for unknown path /some/random/route', () => {
    renderWithRoute('/some/random/route')
    expect(screen.getByText(/error 404/i)).toBeInTheDocument()
    expect(screen.getAllByText(/page not found/i).length).toBeGreaterThanOrEqual(1)
  })

  it('renders Creator Studio breadcrumb and title at /creator', () => {
    renderWithRoute('/creator')
    expect(screen.getByText(/Authoring \//i)).toBeInTheDocument()
    expect(screen.getAllByRole('heading', { level: 1, name: /Creator Studio/i }).length).toBeGreaterThanOrEqual(1)
    expect(screen.queryByText(/404 \//i)).not.toBeInTheDocument()
  })
})
