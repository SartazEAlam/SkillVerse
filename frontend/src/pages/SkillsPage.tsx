import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Network,
  ListFilter,
  Layers,
  ArrowRight,
  Info,
  CheckCircle2,
  Lock,
  ExternalLink,
  Sparkles,
  MoveRight
} from 'lucide-react'
import { SAMPLE_SKILLS, SKILL_CATEGORIES } from '../data/skills'
import type { Skill } from '../types/skill'
import { Card } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'

// Deterministic focused coordinates when viewing a single category
const SINGLE_CATEGORY_COORDS: Record<string, Record<string, { x: number; y: number }>> = {
  tech: {
    'skill-html': { x: 16, y: 50 },
    'skill-css-flex': { x: 50, y: 26 },
    'skill-js-dom': { x: 50, y: 74 },
    'skill-responsive-arch': { x: 84, y: 26 },
    'skill-async-web': { x: 84, y: 74 }
  },
  communication: {
    'skill-active-listening': { x: 16, y: 50 },
    'skill-standup-articulation': { x: 50, y: 50 },
    'skill-executive-briefing': { x: 84, y: 26 },
    'skill-diplomatic-negotiation': { x: 84, y: 74 }
  },
  productivity: {
    'skill-time-audit': { x: 16, y: 50 },
    'skill-deep-work': { x: 50, y: 26 },
    'skill-priority-matrices': { x: 50, y: 74 },
    'skill-personal-os': { x: 84, y: 50 }
  },
  design: {
    'skill-type-rhythm': { x: 26, y: 50 },
    'skill-design-tokens': { x: 74, y: 50 }
  }
}

const SWIMLANES = [
  { id: 'tech', label: 'Programming & Web', color: '#8B5CF6', topPct: 0, heightPct: 25 },
  { id: 'communication', label: 'Spoken Communication', color: '#06B6D4', topPct: 25, heightPct: 25 },
  { id: 'productivity', label: 'Productivity & Systems', color: '#10B981', topPct: 50, heightPct: 25 },
  { id: 'design', label: 'Design & Visual Hierarchy', color: '#F59E0B', topPct: 75, heightPct: 25 }
]

export const SkillsPage: React.FC = () => {
  const [viewMode, setViewMode] = useState<'visual' | 'list'>('visual')
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [activeSkill, setActiveSkill] = useState<Skill | null>(SAMPLE_SKILLS[0])

  const filteredSkills = SAMPLE_SKILLS.filter(
    (skill) => selectedCategory === 'all' || skill.categoryId === selectedCategory
  )

  const handleCategoryChange = (catId: string) => {
    setSelectedCategory(catId)
    if (catId !== 'all') {
      const skillsInCat = SAMPLE_SKILLS.filter((s) => s.categoryId === catId)
      if (skillsInCat.length > 0 && activeSkill?.categoryId !== catId) {
        setActiveSkill(skillsInCat[0])
      }
    }
  }

  const getCanvasHeight = () => {
    if (selectedCategory === 'all') return 760
    if (selectedCategory === 'design') return 320
    return 400
  }

  const canvasHeight = getCanvasHeight()

  const getSkillCoord = (skill: Skill) => {
    if (selectedCategory !== 'all' && SINGLE_CATEGORY_COORDS[selectedCategory]?.[skill.id]) {
      return SINGLE_CATEGORY_COORDS[selectedCategory][skill.id]
    }
    return { x: skill.x ?? 50, y: skill.y ?? 50 }
  }

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-border-subtle pb-6">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Badge variant="cyan" size="sm" icon={<Network className="w-3 h-3" />}>
              Taxonomy Explorer
            </Badge>
            <Badge variant="violet" size="sm">
              Demonstration Map
            </Badge>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-text-primary tracking-tight">
            Cross-Disciplinary Skill Map
          </h1>
          <p className="text-sm text-text-secondary mt-1 max-w-2xl">
            Explore how foundational competencies connect and unlock advanced capabilities across programming, verbal communication, systems thinking, and interface design.
          </p>
        </div>

        {/* View Mode Switcher (Visual Graph vs Accessible List) */}
        <div className="flex items-center p-1 rounded-xl bg-bg-surface border border-border-subtle shrink-0">
          <button
            type="button"
            onClick={() => setViewMode('visual')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer ${
              viewMode === 'visual'
                ? 'bg-accent-violet text-white shadow-sm'
                : 'text-text-secondary hover:text-text-primary'
            }`}
          >
            <Network className="w-3.5 h-3.5" />
            <span>Visual Map</span>
          </button>
          <button
            type="button"
            onClick={() => setViewMode('list')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer ${
              viewMode === 'list'
                ? 'bg-accent-violet text-white shadow-sm'
                : 'text-text-secondary hover:text-text-primary'
            }`}
          >
            <ListFilter className="w-3.5 h-3.5" />
            <span>Accessible List</span>
          </button>
        </div>
      </div>

      {/* Demo Notice Banner */}
      <div className="p-3.5 rounded-xl bg-bg-elevated border border-border-subtle flex items-start gap-3 text-xs text-text-secondary">
        <Info className="w-4 h-4 text-accent-cyan shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-text-primary">Demonstration Data Notice: </span>
          The mastery percentages, unlock states, and sample prerequisites shown here demonstrate the planned skill progression engine. Real learner mastery evaluation begins in Phase 6.
        </div>
      </div>

      {/* Category Filter Chips */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs font-medium text-text-muted mr-1">Discipline:</span>
        <button
          type="button"
          onClick={() => handleCategoryChange('all')}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer ${
            selectedCategory === 'all'
              ? 'bg-text-primary text-black font-semibold'
              : 'bg-bg-surface text-text-secondary hover:text-text-primary border border-border-subtle'
          }`}
        >
          All Disciplines
        </button>
        {SKILL_CATEGORIES.map((cat) => (
          <button
            key={cat.id}
            type="button"
            onClick={() => handleCategoryChange(cat.id)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer flex items-center gap-1.5 ${
              selectedCategory === cat.id
                ? 'bg-accent-violet text-white shadow-sm'
                : 'bg-bg-surface text-text-secondary hover:text-text-primary border border-border-subtle'
            }`}
          >
            <span
              className="w-2 h-2 rounded-full"
              style={{ backgroundColor: cat.color }}
            />
            <span>{cat.name}</span>
          </button>
        ))}
      </div>

      {/* Main Content Area */}
      {viewMode === 'visual' ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Visual SVG Map Container (2 cols) */}
          <div className="lg:col-span-2 space-y-3">
            <Card variant="inset" className="p-0 overflow-hidden relative border-border-medium flex flex-col">
              {/* Legend & Instructions Bar */}
              <div className="p-3.5 border-b border-border-subtle bg-bg-surface/50 flex flex-wrap items-center justify-between gap-2 text-xs text-text-muted">
                <div className="flex items-center gap-4">
                  <span className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-state-success" />
                    <span>Foundational</span>
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-accent-cyan" />
                    <span>Intermediate</span>
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-accent-violet" />
                    <span>Advanced</span>
                  </span>
                </div>
                <span className="font-mono text-[11px] text-text-secondary hidden sm:inline-block">
                  Click any node to inspect prerequisites & objectives
                </span>
              </div>

              {/* Mobile Swipe Hint */}
              <div className="md:hidden p-2 bg-bg-surface/30 border-b border-border-subtle flex items-center gap-2 text-[11px] text-text-muted px-4">
                <MoveRight className="w-3.5 h-3.5 text-accent-cyan shrink-0" />
                <span>Swipe horizontally to view full progression tiers</span>
              </div>

              {/* Scrollable Canvas Area */}
              <div className="overflow-x-auto overflow-y-hidden p-2 sm:p-4">
                <div
                  className="relative min-w-[720px] w-full"
                  style={{ height: `${canvasHeight}px` }}
                >
                  {/* Swimlane Backgrounds (when viewing all disciplines) */}
                  {selectedCategory === 'all' &&
                    SWIMLANES.map((lane) => (
                      <div
                        key={lane.id}
                        className="absolute left-0 right-0 border-b border-border-subtle/40 pointer-events-none"
                        style={{
                          top: `${lane.topPct}%`,
                          height: `${lane.heightPct}%`
                        }}
                      >
                        <div className="p-2 sm:p-3 flex items-center gap-2">
                          <span
                            className="w-2 h-2 rounded-full"
                            style={{ backgroundColor: lane.color }}
                          />
                          <span className="text-[11px] font-mono uppercase tracking-wider text-text-muted font-semibold">
                            {lane.label}
                          </span>
                        </div>
                      </div>
                    ))}

                  {/* SVG Connection Lines */}
                  <svg
                    className="absolute inset-0 w-full h-full pointer-events-none"
                    viewBox={`0 0 1000 ${canvasHeight}`}
                    preserveAspectRatio="none"
                    aria-hidden="true"
                  >
                    <defs>
                      <marker
                        id="arrow-default"
                        viewBox="0 0 10 10"
                        refX="6"
                        refY="5"
                        markerWidth="5"
                        markerHeight="5"
                        orient="auto-start-reverse"
                      >
                        <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="rgba(255,255,255,0.25)" />
                      </marker>
                      <marker
                        id="arrow-unlocks"
                        viewBox="0 0 10 10"
                        refX="6"
                        refY="5"
                        markerWidth="6"
                        markerHeight="6"
                        orient="auto-start-reverse"
                      >
                        <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#8B5CF6" />
                      </marker>
                      <marker
                        id="arrow-prereq"
                        viewBox="0 0 10 10"
                        refX="6"
                        refY="5"
                        markerWidth="6"
                        markerHeight="6"
                        orient="auto-start-reverse"
                      >
                        <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#06B6D4" />
                      </marker>
                    </defs>

                    {filteredSkills.map((skill) => {
                      const coord1 = getSkillCoord(skill)
                      const x1 = (coord1.x / 100) * 1000
                      const y1 = (coord1.y / 100) * canvasHeight

                      return skill.unlockedSkills.map((targetId) => {
                        const targetSkill = filteredSkills.find((s) => s.id === targetId)
                        if (!targetSkill) return null

                        const coord2 = getSkillCoord(targetSkill)
                        const x2 = (coord2.x / 100) * 1000
                        const y2 = (coord2.y / 100) * canvasHeight

                        // Node half-width offset in SVG units so lines start/end at card borders
                        const startX = x1 + 95
                        const endX = x2 - 95

                        const dx = (endX - startX) * 0.5
                        const pathD = `M ${startX} ${y1} C ${startX + dx} ${y1}, ${endX - dx} ${y2}, ${endX} ${y2}`

                        const isOutFromActive = activeSkill?.id === skill.id
                        const isInToActive = activeSkill?.id === targetSkill.id

                        let strokeColor = 'rgba(255,255,255,0.16)'
                        let strokeWidth = 1.5
                        let markerEnd = 'url(#arrow-default)'

                        if (isOutFromActive) {
                          strokeColor = '#8B5CF6'
                          strokeWidth = 2.5
                          markerEnd = 'url(#arrow-unlocks)'
                        } else if (isInToActive) {
                          strokeColor = '#06B6D4'
                          strokeWidth = 2.5
                          markerEnd = 'url(#arrow-prereq)'
                        }

                        return (
                          <path
                            key={`${skill.id}-${targetId}`}
                            d={pathD}
                            fill="none"
                            stroke={strokeColor}
                            strokeWidth={strokeWidth}
                            markerEnd={markerEnd}
                            strokeDasharray={skill.level === 'Advanced' ? '4 4' : undefined}
                          />
                        )
                      })
                    })}
                  </svg>

                  {/* Interactive Skill Node Cards */}
                  {filteredSkills.map((skill) => {
                    const coord = getSkillCoord(skill)
                    const isSelected = activeSkill?.id === skill.id
                    const isPrereqOfActive = activeSkill?.prerequisites.includes(skill.id)
                    const isUnlockedByActive = activeSkill?.unlockedSkills.includes(skill.id)

                    const levelBorderColor =
                      skill.level === 'Foundational'
                        ? 'border-state-success'
                        : skill.level === 'Intermediate'
                        ? 'border-accent-cyan'
                        : 'border-accent-violet'

                    const levelDotColor =
                      skill.level === 'Foundational'
                        ? 'bg-state-success'
                        : skill.level === 'Intermediate'
                        ? 'bg-accent-cyan'
                        : 'bg-accent-violet'

                    return (
                      <button
                        key={skill.id}
                        type="button"
                        onClick={() => setActiveSkill(skill)}
                        style={{
                          left: `${coord.x}%`,
                          top: `${coord.y}%`,
                          transform: 'translate(-50%, -50%)'
                        }}
                        className={`absolute w-[170px] sm:w-[185px] p-2.5 sm:p-3 rounded-xl text-left transition-all duration-200 cursor-pointer select-none group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-violet focus-visible:ring-offset-2 focus-visible:ring-offset-bg-base ${
                          isSelected
                            ? 'bg-bg-elevated border-2 shadow-xl shadow-accent-violet/30 scale-105 z-20 ' + levelBorderColor
                            : isPrereqOfActive
                            ? 'bg-bg-elevated/95 border-2 border-accent-cyan shadow-md shadow-accent-cyan/20 z-15'
                            : isUnlockedByActive
                            ? 'bg-bg-elevated/95 border-2 border-accent-violet shadow-md shadow-accent-violet/20 z-15'
                            : 'bg-bg-elevated/95 hover:bg-bg-elevated border border-border-medium hover:border-text-primary z-10'
                        }`}
                        aria-pressed={isSelected}
                        aria-label={`${skill.name}, ${skill.level} skill, ${skill.sampleMasteryPct}% sample mastery`}
                      >
                        <div className="flex items-center justify-between gap-1 mb-1">
                          <div className="flex items-center gap-1.5">
                            <span className={`w-2 h-2 rounded-full shrink-0 ${levelDotColor}`} />
                            <span className="text-[10px] uppercase font-mono tracking-wider text-text-muted">
                              {skill.level}
                            </span>
                          </div>
                          <span className="text-[10px] font-mono text-accent-cyan font-semibold">
                            {skill.sampleMasteryPct}%
                          </span>
                        </div>
                        <p className="text-xs font-semibold text-text-primary leading-snug line-clamp-2">
                          {skill.name}
                        </p>
                      </button>
                    )
                  })}
                </div>
              </div>
            </Card>
          </div>

          {/* Skill Detail Panel (1 col) */}
          <div className="space-y-4">
            {activeSkill ? (
              <Card variant="elevated" className="space-y-5">
                <div>
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <Badge
                      variant={
                        activeSkill.level === 'Foundational'
                          ? 'emerald'
                          : activeSkill.level === 'Intermediate'
                          ? 'cyan'
                          : 'violet'
                      }
                      size="sm"
                    >
                      {activeSkill.level}
                    </Badge>
                    <span className="text-xs font-mono text-text-muted">
                      Demo Score: <strong className="text-text-primary">{activeSkill.sampleMasteryPct}%</strong>
                    </span>
                  </div>

                  <h3 className="text-xl font-bold text-text-primary">
                    {activeSkill.name}
                  </h3>
                  <p className="text-xs text-text-secondary mt-2 leading-relaxed">
                    {activeSkill.description}
                  </p>
                </div>

                {/* Prerequisites */}
                <div className="pt-4 border-t border-border-subtle space-y-2">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-text-muted flex items-center gap-1.5">
                    <Layers className="w-3.5 h-3.5 text-accent-violet" />
                    <span>Prerequisites</span>
                  </h4>
                  {activeSkill.prerequisites.length > 0 ? (
                    <div className="space-y-1.5">
                      {activeSkill.prerequisites.map((prereqId) => {
                        const prereq = SAMPLE_SKILLS.find((s) => s.id === prereqId)
                        if (!prereq) return null
                        return (
                          <div
                            key={prereq.id}
                            className="p-2 rounded-lg bg-bg-surface border border-border-subtle flex items-center justify-between text-xs cursor-pointer hover:border-accent-violet transition-colors"
                            onClick={() => setActiveSkill(prereq)}
                          >
                            <span className="font-medium text-text-primary">{prereq.name}</span>
                            <span className="text-[10px] font-mono text-state-success flex items-center gap-1">
                              <CheckCircle2 className="w-3 h-3" /> Met
                            </span>
                          </div>
                        )
                      })}
                    </div>
                  ) : (
                    <p className="text-xs text-text-muted italic">
                      None • This is an entry-level foundational skill.
                    </p>
                  )}
                </div>

                {/* Unlocks */}
                <div className="pt-4 border-t border-border-subtle space-y-2">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-text-muted flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-accent-cyan" />
                    <span>Unlocks Next</span>
                  </h4>
                  {activeSkill.unlockedSkills.length > 0 ? (
                    <div className="space-y-1.5">
                      {activeSkill.unlockedSkills.map((unlockId) => {
                        const nextSkill = SAMPLE_SKILLS.find((s) => s.id === unlockId)
                        if (!nextSkill) return null
                        return (
                          <div
                            key={nextSkill.id}
                            className="p-2 rounded-lg bg-bg-surface border border-border-subtle flex items-center justify-between text-xs cursor-pointer hover:border-accent-cyan transition-colors"
                            onClick={() => setActiveSkill(nextSkill)}
                          >
                            <span className="font-medium text-text-primary">{nextSkill.name}</span>
                            <span className="text-[10px] font-mono text-accent-cyan flex items-center gap-1">
                              <Lock className="w-3 h-3" /> Ready
                            </span>
                          </div>
                        )
                      })}
                    </div>
                  ) : (
                    <p className="text-xs text-text-muted italic">
                      Terminal node in the current Phase 1 curriculum map.
                    </p>
                  )}
                </div>

                {/* Associated Courses */}
                <div className="pt-4 border-t border-border-subtle space-y-2">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-text-muted">
                    Learn in Courses
                  </h4>
                  {activeSkill.courseSlugs.map((slug) => (
                    <Link key={slug} to={`/courses/${slug}`}>
                      <Button variant="outline" size="sm" className="w-full justify-between" rightIcon={<ExternalLink className="w-3.5 h-3.5" />}>
                        <span className="truncate">Explore Course Outline</span>
                      </Button>
                    </Link>
                  ))}
                </div>
              </Card>
            ) : (
              <Card variant="surface" className="text-center p-6 text-text-muted text-xs">
                Select a skill from the graph to inspect its prerequisites and objectives.
              </Card>
            )}
          </div>
        </div>
      ) : (
        /* Accessible Structured List View */
        <div className="space-y-6">
          <div className="text-xs text-text-secondary bg-bg-surface/50 p-3 rounded-lg border border-border-subtle">
            Accessible Structured Tree: All skills organized by category, hierarchy level, and prerequisite relationships.
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {SKILL_CATEGORIES.map((category) => {
              const catSkills = filteredSkills.filter((s) => s.categoryId === category.id)
              if (catSkills.length === 0) return null

              return (
                <Card key={category.id} variant="elevated" className="space-y-4">
                  <div className="border-b border-border-subtle pb-3 flex items-center justify-between">
                    <div>
                      <h2 className="text-base font-bold text-text-primary flex items-center gap-2">
                        <span
                          className="w-2.5 h-2.5 rounded-full"
                          style={{ backgroundColor: category.color }}
                        />
                        <span>{category.name}</span>
                      </h2>
                      <p className="text-xs text-text-muted mt-0.5">{category.description}</p>
                    </div>
                    <Badge variant="default" size="sm">
                      {catSkills.length} skills
                    </Badge>
                  </div>

                  <div className="space-y-3">
                    {catSkills.map((skill) => (
                      <div
                        key={skill.id}
                        className="p-3.5 rounded-xl bg-bg-surface border border-border-subtle hover:border-border-medium transition-all space-y-2"
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <span className="text-xs font-bold text-text-primary">
                              {skill.name}
                            </span>
                            <p className="text-xs text-text-secondary mt-1">
                              {skill.description}
                            </p>
                          </div>
                          <Badge
                            variant={
                              skill.level === 'Foundational'
                                ? 'emerald'
                                : skill.level === 'Intermediate'
                                ? 'cyan'
                                : 'violet'
                            }
                            size="sm"
                          >
                            {skill.level}
                          </Badge>
                        </div>

                        {/* Prerequisites indicator */}
                        {skill.prerequisites.length > 0 && (
                          <div className="text-[11px] text-text-muted">
                            <span className="font-semibold text-text-secondary">Requires: </span>
                            {skill.prerequisites
                              .map((id) => SAMPLE_SKILLS.find((s) => s.id === id)?.name)
                              .filter(Boolean)
                              .join(', ')}
                          </div>
                        )}

                        {/* Actions */}
                        <div className="pt-2 border-t border-border-subtle flex items-center justify-between text-xs">
                          <span className="font-mono text-[11px] text-text-muted">
                            Sample Mastery: <strong className="text-accent-cyan">{skill.sampleMasteryPct}%</strong>
                          </span>
                          <Link
                            to={`/courses/${skill.courseSlugs[0] || 'web-dev-foundations'}`}
                            className="text-accent-violet hover:underline flex items-center gap-1 font-medium"
                          >
                            <span>Course</span>
                            <ArrowRight className="w-3 h-3" />
                          </Link>
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}

