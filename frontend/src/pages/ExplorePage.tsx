import React, { useState, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { Search, Compass, Clock, Layers, ArrowRight, RotateCcw } from 'lucide-react'
import { SAMPLE_COURSES, COURSE_CATEGORIES } from '../data/courses'
import { Card } from '../components/ui/Card'
import { Input } from '../components/ui/Input'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { EmptyState } from '../components/ui/EmptyState'

export const ExplorePage: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [selectedLevel, setSelectedLevel] = useState<string>('all')

  const filteredCourses = useMemo(() => {
    return SAMPLE_COURSES.filter((course) => {
      // Category filter
      const matchesCategory =
        selectedCategory === 'all' || course.categoryId === selectedCategory

      // Level filter
      const matchesLevel =
        selectedLevel === 'all' || course.level.toLowerCase() === selectedLevel.toLowerCase()

      // Search query (matches title, shortDescription, or skillsTaught)
      const q = searchQuery.toLowerCase().trim()
      const matchesSearch =
        !q ||
        course.title.toLowerCase().includes(q) ||
        course.shortDescription.toLowerCase().includes(q) ||
        course.skillsTaught.some((skill) => skill.toLowerCase().includes(q))

      return matchesCategory && matchesLevel && matchesSearch
    })
  }, [searchQuery, selectedCategory, selectedLevel])

  const handleResetFilters = () => {
    setSearchQuery('')
    setSelectedCategory('all')
    setSelectedLevel('all')
  }

  const hasActiveFilters = searchQuery !== '' || selectedCategory !== 'all' || selectedLevel !== 'all'

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-border-subtle pb-6">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Badge variant="cyan" size="sm" icon={<Compass className="w-3 h-3" />}>
              Course Catalog
            </Badge>
            <span className="text-xs font-mono text-text-muted">
              Phase 1 Curriculum
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-text-primary tracking-tight">
            Explore Interactive Courses
          </h1>
          <p className="text-sm text-text-secondary mt-1 max-w-2xl">
            Choose a chapter-based learning track with live execution environments and real-time assessments across software, communication, and systems thinking.
          </p>
        </div>

        {hasActiveFilters && (
          <Button
            variant="ghost"
            size="sm"
            onClick={handleResetFilters}
            leftIcon={<RotateCcw className="w-3.5 h-3.5" />}
          >
            Reset Filters
          </Button>
        )}
      </div>

      {/* Filter and Search Controls Bar */}
      <div className="space-y-4">
        {/* Search input */}
        <div className="max-w-xl">
          <Input
            placeholder="Search courses, topics, or skills (e.g. flexbox, standup, deep work)..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onClear={() => setSearchQuery('')}
            leftIcon={<Search className="w-4 h-4" />}
            aria-label="Search courses"
          />
        </div>

        {/* Category Filter Chips */}
        <div className="flex flex-wrap items-center gap-2 pt-1">
          <span className="text-xs font-medium text-text-muted mr-1">Category:</span>
          {COURSE_CATEGORIES.map((cat) => {
            const isSelected = selectedCategory === cat.id
            return (
              <button
                key={cat.id}
                type="button"
                onClick={() => setSelectedCategory(cat.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer select-none ${
                  isSelected
                    ? 'bg-accent-violet text-white shadow-sm shadow-accent-violet/30'
                    : 'bg-bg-surface text-text-secondary hover:text-text-primary hover:bg-bg-elevated border border-border-subtle'
                }`}
              >
                {cat.name}
              </button>
            )
          })}
        </div>

        {/* Level Filter Chips */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-medium text-text-muted mr-1">Difficulty:</span>
          {['all', 'beginner', 'intermediate', 'advanced'].map((lvl) => {
            const isSelected = selectedLevel === lvl
            return (
              <button
                key={lvl}
                type="button"
                onClick={() => setSelectedLevel(lvl)}
                className={`px-2.5 py-1 rounded-md text-[11px] font-mono uppercase tracking-wider transition-all cursor-pointer select-none ${
                  isSelected
                    ? 'bg-accent-cyan text-black font-semibold'
                    : 'bg-bg-surface/50 text-text-muted hover:text-text-primary border border-border-subtle'
                }`}
              >
                {lvl}
              </button>
            )
          })}
        </div>
      </div>

      {/* Results Header */}
      <div className="flex items-center justify-between text-xs text-text-muted font-mono">
        <span data-testid="results-count">
          Showing {filteredCourses.length} of {SAMPLE_COURSES.length} courses
        </span>
        {searchQuery && (
          <span>
            Query: "<span className="text-accent-violet">{searchQuery}</span>"
          </span>
        )}
      </div>

      {/* Course Cards Grid */}
      {filteredCourses.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredCourses.map((course) => (
            <Card
              key={course.id}
              variant="elevated"
              hoverEffect
              className="flex flex-col justify-between group"
            >
              <div>
                {/* Meta header */}
                <div className="flex items-center justify-between gap-2 mb-3">
                  <Badge variant="cyan" size="sm">
                    {course.categoryName}
                  </Badge>
                  <span className="text-xs font-mono text-text-muted px-2 py-0.5 rounded bg-bg-surface border border-border-subtle">
                    {course.level}
                  </span>
                </div>

                {/* Course Title */}
                <h2 className="text-lg font-bold text-text-primary mb-2 group-hover:text-accent-violet transition-colors">
                  {course.title}
                </h2>

                {/* Description */}
                <p className="text-xs text-text-secondary leading-relaxed line-clamp-3 mb-4">
                  {course.shortDescription}
                </p>

                {/* Skills tags preview */}
                <div className="flex flex-wrap gap-1.5 mb-5">
                  {course.skillsTaught.map((skill) => (
                    <span
                      key={skill}
                      className="text-[10px] font-mono px-2 py-0.5 rounded bg-bg-surface text-text-muted border border-border-subtle"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>

              {/* Card Footer */}
              <div className="pt-4 border-t border-border-subtle flex items-center justify-between gap-2">
                <div className="flex items-center gap-3 text-xs text-text-muted font-mono">
                  <span className="flex items-center gap-1" title="Estimated completion time">
                    <Clock className="w-3.5 h-3.5 text-text-muted" />
                    {course.estimatedHours}h
                  </span>
                  <span className="flex items-center gap-1" title="Modules count">
                    <Layers className="w-3.5 h-3.5 text-text-muted" />
                    {course.modulesCount} mods
                  </span>
                </div>

                <Link to={`/courses/${course.slug}`}>
                  <Button variant="primary" size="sm" rightIcon={<ArrowRight className="w-3.5 h-3.5" />}>
                    View Course
                  </Button>
                </Link>
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <EmptyState
          icon={<Compass className="w-6 h-6" />}
          title="No matching courses found"
          description="We couldn't find any courses matching your search query or selected filters. Try searching for different keywords or resetting your filters."
          action={
            <Button variant="outline" size="sm" onClick={handleResetFilters} leftIcon={<RotateCcw className="w-4 h-4" />}>
              Reset all filters
            </Button>
          }
        />
      )}
    </div>
  )
}
