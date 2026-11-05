import React, { useEffect, useState, useCallback } from 'react'
import {
  FolderGit2,
  AlertCircle,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'
import type { ApiDiscipline } from '../types/catalog'
import type { ProjectFilterParams, ProjectPaginatedResponse } from '../types/project'
import { projectApi } from '../services/projectApi'
import { ProjectCard } from '../features/projects/ProjectCard'
import { ProjectFilters } from '../features/projects/ProjectFilters'

export const ProjectsPage: React.FC = () => {
  const [data, setData] = useState<ProjectPaginatedResponse | null>(null)
  const [disciplines, setDisciplines] = useState<ApiDiscipline[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [filters, setFilters] = useState<ProjectFilterParams>({
    page: 1,
    page_size: 12,
    sort_by: 'created_at',
    sort_order: 'desc',
  })

  // Fetch disciplines once for filter dropdown
  useEffect(() => {
    let mounted = true
    projectApi
      .listDisciplines()
      .then((res) => {
        if (mounted) setDisciplines(res)
      })
      .catch(() => {
        // Disciplines error is non-fatal
      })
    return () => {
      mounted = false
    }
  }, [])

  // Fetch projects whenever filters change
  const fetchProjects = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await projectApi.listProjects(filters)
      setData(res)
    } catch (err: unknown) {
      setError(
        err instanceof Error
          ? err.message
          : 'Failed to load projects. Please check your connection and retry.'
      )
    } finally {
      setLoading(false)
    }
  }, [filters])

  useEffect(() => {
    fetchProjects()
  }, [fetchProjects])

  const handleFilterChange = (newFilters: Partial<ProjectFilterParams>) => {
    setFilters((prev) => ({
      ...prev,
      ...newFilters,
      page: newFilters.page ?? 1,
    }))
  }

  const handleResetFilters = () => {
    setFilters({
      page: 1,
      page_size: 12,
      sort_by: 'created_at',
      sort_order: 'desc',
    })
  }

  const handlePageChange = (newPage: number) => {
    if (newPage < 1 || (data && newPage > data.pages)) return
    setFilters((prev) => ({ ...prev, page: newPage }))
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <main className="min-h-screen bg-bg-base py-8 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto space-y-8">
      {/* Hero Header */}
      <div className="relative overflow-hidden rounded-2xl border border-border-subtle bg-gradient-to-br from-bg-elevated via-bg-surface to-bg-elevated/80 p-6 sm:p-8 md:p-10 shadow-lg">
        <div className="relative z-10 max-w-3xl space-y-3">
          <div className="inline-flex items-center gap-2 rounded-full border border-accent-cyan/30 bg-accent-cyan/10 px-3 py-1 text-xs font-semibold text-accent-cyan">
            <FolderGit2 className="h-3.5 w-3.5" aria-hidden="true" />
            <span>Applied Mastery Capstones</span>
          </div>

          <h1 className="text-2xl sm:text-3xl md:text-4xl font-extrabold tracking-tight text-text-primary">
            Practical Projects & Capstones
          </h1>

          <p className="text-sm sm:text-base text-text-secondary leading-relaxed">
            Apply cross-disciplinary skills to build real software, architectural designs, and
            workplace communication deliverables. Submissions are rigorously evaluated against rubric
            standards with verifiable portfolio artifacts.
          </p>
        </div>

        {/* Ambient background decoration */}
        <div
          aria-hidden="true"
          className="absolute -right-20 -bottom-20 h-64 w-64 rounded-full bg-accent-violet/10 blur-3xl pointer-events-none"
        />
        <div
          aria-hidden="true"
          className="absolute right-40 top-0 h-48 w-48 rounded-full bg-accent-cyan/10 blur-2xl pointer-events-none"
        />
      </div>

      {/* Filter and Search Bar */}
      <ProjectFilters
        filters={filters}
        disciplines={disciplines}
        onFilterChange={handleFilterChange}
        onReset={handleResetFilters}
        totalResults={data?.total ?? 0}
      />

      {/* Main Content: Loading, Error, Empty, or Grid */}
      {loading ? (
        <div className="space-y-6" aria-busy="true" aria-label="Loading projects">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {Array.from({ length: 6 }).map((_, idx) => (
              <div
                key={idx}
                className="h-64 rounded-xl border border-border-subtle bg-bg-elevated/40 p-6 animate-pulse space-y-4"
              >
                <div className="flex justify-between">
                  <div className="h-5 w-24 rounded bg-bg-surface" />
                  <div className="h-5 w-16 rounded bg-bg-surface" />
                </div>
                <div className="h-6 w-3/4 rounded bg-bg-surface" />
                <div className="space-y-2">
                  <div className="h-4 w-full rounded bg-bg-surface" />
                  <div className="h-4 w-5/6 rounded bg-bg-surface" />
                </div>
                <div className="pt-4 flex gap-2">
                  <div className="h-6 w-20 rounded bg-bg-surface" />
                  <div className="h-6 w-20 rounded bg-bg-surface" />
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : error ? (
        <div
          role="alert"
          className="rounded-2xl border border-state-error/30 bg-state-error/5 p-8 text-center space-y-4"
        >
          <div className="inline-flex rounded-full bg-state-error/10 p-3 text-state-error">
            <AlertCircle className="h-8 w-8" aria-hidden="true" />
          </div>
          <h2 className="text-lg font-semibold text-text-primary">Unable to Load Projects</h2>
          <p className="text-sm text-text-secondary max-w-md mx-auto">{error}</p>
          <button
            type="button"
            onClick={fetchProjects}
            className="inline-flex items-center gap-2 rounded-lg bg-accent-violet px-4 py-2 text-sm font-semibold text-white hover:bg-accent-violet-hover transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-violet cursor-pointer"
          >
            <RefreshCw className="h-4 w-4" aria-hidden="true" />
            <span>Retry Connection</span>
          </button>
        </div>
      ) : !data || data.items.length === 0 ? (
        <div className="rounded-2xl border border-border-subtle bg-bg-elevated/40 p-12 text-center space-y-4">
          <div className="inline-flex rounded-full bg-bg-surface p-4 text-text-muted">
            <FolderGit2 className="h-8 w-8" aria-hidden="true" />
          </div>
          <h2 className="text-lg font-semibold text-text-primary">No Matching Projects Found</h2>
          <p className="text-sm text-text-secondary max-w-md mx-auto">
            We couldn't find any practical projects matching your search and filter criteria. Try
            adjusting your filters or clearing your query.
          </p>
          <button
            type="button"
            onClick={handleResetFilters}
            className="inline-flex items-center gap-2 rounded-lg border border-border-subtle bg-bg-surface px-4 py-2 text-sm font-medium text-text-primary hover:bg-bg-elevated transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-violet cursor-pointer"
          >
            <span>Reset All Filters</span>
          </button>
        </div>
      ) : (
        <div className="space-y-8">
          {/* Projects Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {data.items.map((project) => (
              <ProjectCard key={project.id} project={project} />
            ))}
          </div>

          {/* Pagination Controls */}
          {data.pages > 1 && (
            <nav
              aria-label="Projects pagination"
              className="flex items-center justify-between border-t border-border-subtle pt-6"
            >
              <button
                type="button"
                onClick={() => handlePageChange(data.page - 1)}
                disabled={data.page <= 1}
                className="inline-flex items-center gap-1.5 rounded-lg border border-border-subtle bg-bg-surface px-3 py-2 text-xs font-medium text-text-primary hover:bg-bg-elevated disabled:opacity-40 disabled:cursor-not-allowed transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-violet cursor-pointer"
                aria-label="Go to previous page"
              >
                <ChevronLeft className="h-4 w-4" aria-hidden="true" />
                <span>Previous</span>
              </button>

              <div className="text-xs text-text-muted font-mono">
                Page <span className="font-semibold text-text-primary">{data.page}</span> of{' '}
                <span className="font-semibold text-text-primary">{data.pages}</span>
              </div>

              <button
                type="button"
                onClick={() => handlePageChange(data.page + 1)}
                disabled={data.page >= data.pages}
                className="inline-flex items-center gap-1.5 rounded-lg border border-border-subtle bg-bg-surface px-3 py-2 text-xs font-medium text-text-primary hover:bg-bg-elevated disabled:opacity-40 disabled:cursor-not-allowed transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-violet cursor-pointer"
                aria-label="Go to next page"
              >
                <span>Next</span>
                <ChevronRight className="h-4 w-4" aria-hidden="true" />
              </button>
            </nav>
          )}
        </div>
      )}
    </main>
  )
}
