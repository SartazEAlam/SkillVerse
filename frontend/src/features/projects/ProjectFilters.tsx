import React from 'react'
import { Search, RotateCcw, Filter, ArrowUpDown } from 'lucide-react'
import type { ApiDiscipline } from '../../types/catalog'
import type { ProjectFilterParams } from '../../types/project'

interface ProjectFiltersProps {
  filters: ProjectFilterParams
  disciplines: ApiDiscipline[]
  onFilterChange: (newFilters: Partial<ProjectFilterParams>) => void
  onReset: () => void
  totalResults: number
}

export const ProjectFilters: React.FC<ProjectFiltersProps> = ({
  filters,
  disciplines,
  onFilterChange,
  onReset,
  totalResults,
}) => {
  const hasActiveFilters = Boolean(
    filters.search ||
      filters.discipline_id ||
      filters.difficulty_level ||
      (filters.sort_by && filters.sort_by !== 'created_at') ||
      (filters.sort_order && filters.sort_order !== 'desc')
  )

  return (
    <div className="rounded-xl border border-border-subtle bg-bg-elevated/60 p-4 backdrop-blur-sm sm:p-5">
      <div className="flex flex-col gap-4">
        {/* Top Row: Search Input & Reset Button */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
          <div className="relative flex-1">
            <label htmlFor="project-search" className="sr-only">
              Search projects by title or description
            </label>
            <Search
              className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted pointer-events-none"
              aria-hidden="true"
            />
            <input
              id="project-search"
              type="search"
              value={filters.search || ''}
              onChange={(e) => onFilterChange({ search: e.target.value, page: 1 })}
              placeholder="Search practical projects by keyword, topic, or tech..."
              className="w-full rounded-lg border border-border-subtle bg-bg-surface pl-10 pr-4 py-2 text-sm text-text-primary placeholder:text-text-muted focus:border-border-focus focus:outline-none focus:ring-1 focus:ring-accent-violet transition-colors"
            />
          </div>

          {hasActiveFilters && (
            <button
              type="button"
              onClick={onReset}
              className="inline-flex items-center justify-center gap-1.5 rounded-lg border border-border-subtle bg-bg-surface px-3 py-2 text-xs font-medium text-text-secondary hover:bg-bg-elevated hover:text-text-primary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-violet cursor-pointer"
              aria-label="Reset all filters"
            >
              <RotateCcw className="h-3.5 w-3.5" aria-hidden="true" />
              <span>Reset Filters</span>
            </button>
          )}
        </div>

        {/* Filter Bar Controls */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 pt-1 border-t border-border-subtle/50">
          {/* Discipline Selector */}
          <div>
            <label
              htmlFor="discipline-filter"
              className="block text-xs font-medium text-text-muted mb-1 flex items-center gap-1"
            >
              <Filter className="h-3 w-3" aria-hidden="true" />
              <span>Discipline</span>
            </label>
            <select
              id="discipline-filter"
              value={filters.discipline_id || ''}
              onChange={(e) =>
                onFilterChange({
                  discipline_id: e.target.value || undefined,
                  page: 1,
                })
              }
              className="w-full rounded-lg border border-border-subtle bg-bg-surface px-3 py-1.5 text-xs text-text-primary focus:border-border-focus focus:outline-none focus:ring-1 focus:ring-accent-violet transition-colors cursor-pointer"
            >
              <option value="">All Disciplines</option>
              {disciplines.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </select>
          </div>

          {/* Difficulty Level Selector */}
          <div>
            <label
              htmlFor="difficulty-filter"
              className="block text-xs font-medium text-text-muted mb-1"
            >
              Difficulty
            </label>
            <select
              id="difficulty-filter"
              value={filters.difficulty_level || ''}
              onChange={(e) =>
                onFilterChange({
                  difficulty_level: e.target.value || undefined,
                  page: 1,
                })
              }
              className="w-full rounded-lg border border-border-subtle bg-bg-surface px-3 py-1.5 text-xs text-text-primary focus:border-border-focus focus:outline-none focus:ring-1 focus:ring-accent-violet transition-colors cursor-pointer"
            >
              <option value="">All Difficulties</option>
              <option value="BEGINNER">Beginner</option>
              <option value="INTERMEDIATE">Intermediate</option>
              <option value="ADVANCED">Advanced</option>
              <option value="EXPERT">Expert</option>
            </select>
          </div>

          {/* Sort By Selector */}
          <div>
            <label
              htmlFor="sort-by-filter"
              className="block text-xs font-medium text-text-muted mb-1 flex items-center gap-1"
            >
              <ArrowUpDown className="h-3 w-3" aria-hidden="true" />
              <span>Sort By</span>
            </label>
            <select
              id="sort-by-filter"
              value={filters.sort_by || 'created_at'}
              onChange={(e) =>
                onFilterChange({
                  sort_by: e.target.value as 'created_at' | 'title' | 'difficulty_level',
                  page: 1,
                })
              }
              className="w-full rounded-lg border border-border-subtle bg-bg-surface px-3 py-1.5 text-xs text-text-primary focus:border-border-focus focus:outline-none focus:ring-1 focus:ring-accent-violet transition-colors cursor-pointer"
            >
              <option value="created_at">Newest Added</option>
              <option value="title">Project Title</option>
              <option value="difficulty_level">Difficulty Level</option>
            </select>
          </div>

          {/* Sort Order Toggle */}
          <div>
            <label
              htmlFor="sort-order-filter"
              className="block text-xs font-medium text-text-muted mb-1"
            >
              Order
            </label>
            <select
              id="sort-order-filter"
              value={filters.sort_order || 'desc'}
              onChange={(e) =>
                onFilterChange({
                  sort_order: e.target.value as 'asc' | 'desc',
                  page: 1,
                })
              }
              className="w-full rounded-lg border border-border-subtle bg-bg-surface px-3 py-1.5 text-xs text-text-primary focus:border-border-focus focus:outline-none focus:ring-1 focus:ring-accent-violet transition-colors cursor-pointer"
            >
              <option value="desc">Descending</option>
              <option value="asc">Ascending</option>
            </select>
          </div>
        </div>

        {/* Results Counter Summary */}
        <div className="flex items-center justify-between text-xs text-text-muted pt-1">
          <span>
            Showing <strong className="text-text-primary">{totalResults}</strong> published project
            {totalResults === 1 ? '' : 's'}
          </span>
          {hasActiveFilters && (
            <span className="text-accent-cyan">Active filters applied</span>
          )}
        </div>
      </div>
    </div>
  )
}

