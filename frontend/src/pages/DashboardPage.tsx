import React, { useEffect, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import {
  Play,
  Flame,
  Target,
  Clock,
  Sparkles,
  ArrowRight,
  BookOpen,
  Code,
  Compass,
  CheckCircle2,
  ShieldCheck,
  TrendingUp,
  Award,
  Zap,
  Trophy,
  Lock,
  RefreshCw,
  FileQuestion,
  Layers,
} from 'lucide-react'
import { SAMPLE_DASHBOARD_DATA } from '../data/dashboard'
import type { DashboardSummary } from '../types/progress'
import { progressApi } from '../services/progressApi'
import { useAuth } from '../context/AuthContext'
import { Card } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { ProgressBar } from '../components/ui/ProgressBar'

export const DashboardPage: React.FC = () => {
  const { user } = useAuth()
  const [dashboardData, setDashboardData] = useState<DashboardSummary | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [isDemo, setIsDemo] = useState<boolean>(false)

  const loadDashboard = useCallback(async () => {
    if (!user) {
      setIsDemo(true)
      setLoading(false)
      return
    }

    setLoading(true)
    try {
      const data = await progressApi.getDashboardSummary()
      setDashboardData(data)
      setIsDemo(false)
    } catch {
      // Fallback to sample data if backend progress is unreachable
      setIsDemo(true)
    } finally {
      setLoading(false)
    }
  }, [user])

  useEffect(() => {
    loadDashboard()
  }, [loadDashboard])

  const learnerName = user?.display_name || user?.email?.split('@')[0] || SAMPLE_DASHBOARD_DATA.learnerName

  const getAchievementIcon = (slug: string) => {
    switch (slug) {
      case 'first_lesson':
        return <Award className="w-5 h-5 text-accent-cyan" />
      case 'fast_learner':
        return <Zap className="w-5 h-5 text-state-warning" />
      case 'first_course':
        return <Trophy className="w-5 h-5 text-accent-violet" />
      case 'perfect_score':
        return <Target className="w-5 h-5 text-state-error" />
      case 'skill_master':
        return <ShieldCheck className="w-5 h-5 text-state-success" />
      case 'polymath':
        return <Sparkles className="w-5 h-5 text-accent-violet" />
      default:
        return <Award className="w-5 h-5 text-accent-cyan" />
    }
  }

  const getActivityTypeIcon = (type: string) => {
    switch (type) {
      case 'code_execution':
        return <Code className="w-3.5 h-3.5 text-accent-violet" />
      case 'single_choice':
      case 'multiple_choice':
        return <FileQuestion className="w-3.5 h-3.5 text-accent-cyan" />
      case 'true_false':
        return <CheckCircle2 className="w-3.5 h-3.5 text-state-success" />
      default:
        return <Layers className="w-3.5 h-3.5 text-text-muted" />
    }
  }

  // Loading skeleton
  if (loading) {
    return (
      <div className="space-y-8 animate-fadeIn p-4 sm:p-6">
        <div className="h-10 w-72 rounded bg-bg-surface animate-pulse" />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 h-72 rounded-2xl bg-bg-surface animate-pulse" />
          <div className="h-72 rounded-2xl bg-bg-surface animate-pulse" />
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-24 rounded-xl bg-bg-surface animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  // 1. Live Authenticated Dashboard
  if (!isDemo && dashboardData) {
    const resumeItem = dashboardData.resume_learning
    const enrolledCourses = dashboardData.enrolled_courses || []
    const achievements = dashboardData.achievements || []
    const recommendations = dashboardData.recommendations || []
    const recentAttempts = dashboardData.recent_attempts || []
    const skills = dashboardData.skills_summary || []

    const masteredSkills = skills.filter((s) => s.status === 'MASTERED')
    const practicingSkills = skills.filter((s) => s.status === 'PRACTICING' || s.status === 'PROVISIONAL')

    return (
      <div className="space-y-8 animate-fadeIn">
        {/* Welcome Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border-subtle pb-6">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-text-primary tracking-tight">
              Welcome back, {learnerName}
            </h1>
            <p className="text-sm text-text-secondary mt-1">
              Live progression active. Every lesson and assessment attempt is verified server-side.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={loadDashboard}
              leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
            >
              Refresh
            </Button>
            <Link to="/explore">
              <Button variant="outline" size="sm" leftIcon={<Compass className="w-4 h-4" />}>
                Catalog
              </Button>
            </Link>
            <Link to="/skills">
              <Button variant="primary" size="sm" rightIcon={<ArrowRight className="w-4 h-4" />}>
                Skill Map
              </Button>
            </Link>
          </div>
        </div>

        {/* Top Grid: Continue Learning Hero & Quick Stats */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Resume Learning Card (2 cols) */}
          <Card variant="elevated" className="lg:col-span-2 relative overflow-hidden flex flex-col justify-between p-6">
            <div className="absolute top-0 right-0 w-96 h-96 bg-accent-violet/5 rounded-full blur-3xl pointer-events-none" />

            {resumeItem ? (
              <>
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <Badge variant="cyan" size="sm" icon={<BookOpen className="w-3 h-3" />}>
                      Active Course
                    </Badge>
                    <span className="text-xs font-mono text-text-muted">
                      {resumeItem.progress_percentage}% completed
                    </span>
                  </div>

                  <h2 className="text-xl font-bold text-text-primary mb-1">
                    {resumeItem.course_title}
                  </h2>
                  <p className="text-sm text-text-secondary mb-3">
                    {resumeItem.module_title}
                  </p>

                  <div className="p-4 rounded-xl bg-bg-surface/80 border border-border-subtle mb-6">
                    <div className="flex items-center gap-2 text-xs font-semibold text-text-primary mb-1">
                      <Code className="w-4 h-4 text-accent-violet" />
                      <span>Next Up: {resumeItem.lesson_title}</span>
                    </div>
                    <p className="text-xs text-text-muted">
                      Pick up directly where you left off. Complete all checkpoint activities to earn verified mastery.
                    </p>
                  </div>
                </div>

                <div className="space-y-4 pt-2 border-t border-border-subtle">
                  <ProgressBar
                    value={resumeItem.progress_percentage}
                    label="Course Completion Progress"
                    showPercentage
                    variant="cyan"
                    size="md"
                  />

                  <div className="flex items-center justify-between pt-1">
                    <span className="text-xs text-text-muted">
                      Continue from {resumeItem.lesson_title}
                    </span>
                    <Link to={`/learn/${resumeItem.course_slug}/${resumeItem.lesson_slug}`}>
                      <Button variant="primary" size="md" leftIcon={<Play className="w-4 h-4 fill-current" />}>
                        Resume Learning
                      </Button>
                    </Link>
                  </div>
                </div>
              </>
            ) : (
              <div className="py-10 text-center space-y-4 flex flex-col items-center justify-center h-full">
                <div className="w-12 h-12 rounded-full bg-accent-violet/10 text-accent-violet flex items-center justify-center">
                  <Compass className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-text-primary">Ready to Begin Your Next Quest?</h3>
                  <p className="text-xs text-text-secondary max-w-sm mx-auto mt-1">
                    You do not have any courses in progress right now. Explore our cross-disciplinary catalog and enroll to start building evidence-backed skills.
                  </p>
                </div>
                <Link to="/explore">
                  <Button variant="primary" size="md" leftIcon={<Compass className="w-4 h-4" />}>
                    Explore Courses
                  </Button>
                </Link>
              </div>
            )}
          </Card>

          {/* Quick Stats Summary Card (1 col) */}
          <Card variant="surface" className="flex flex-col justify-between p-6">
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xs font-bold uppercase tracking-wider text-text-muted flex items-center gap-2">
                  <Target className="w-4 h-4 text-accent-violet" />
                  <span>Progression Overview</span>
                </h3>
                <Badge variant="emerald" size="sm">
                  Live
                </Badge>
              </div>

              <div className="space-y-4 py-2">
                <div className="flex items-center justify-between p-3 rounded-lg bg-bg-inset border border-border-subtle">
                  <div className="flex items-center gap-2 text-xs text-text-secondary">
                    <BookOpen className="w-4 h-4 text-accent-violet" />
                    <span>Enrolled Courses</span>
                  </div>
                  <span className="font-mono font-bold text-text-primary text-base">
                    {enrolledCourses.length}
                  </span>
                </div>

                <div className="flex items-center justify-between p-3 rounded-lg bg-bg-inset border border-border-subtle">
                  <div className="flex items-center gap-2 text-xs text-text-secondary">
                    <ShieldCheck className="w-4 h-4 text-state-success" />
                    <span>Mastered Skills</span>
                  </div>
                  <span className="font-mono font-bold text-text-primary text-base">
                    {masteredSkills.length}
                  </span>
                </div>

                <div className="flex items-center justify-between p-3 rounded-lg bg-bg-inset border border-border-subtle">
                  <div className="flex items-center gap-2 text-xs text-text-secondary">
                    <TrendingUp className="w-4 h-4 text-accent-cyan" />
                    <span>Skills In Progress</span>
                  </div>
                  <span className="font-mono font-bold text-text-primary text-base">
                    {practicingSkills.length}
                  </span>
                </div>

                <div className="flex items-center justify-between p-3 rounded-lg bg-bg-inset border border-border-subtle">
                  <div className="flex items-center gap-2 text-xs text-text-secondary">
                    <Award className="w-4 h-4 text-state-warning" />
                    <span>Achievements</span>
                  </div>
                  <span className="font-mono font-bold text-text-primary text-base">
                    {achievements.filter((a) => a.earned).length} / {achievements.length}
                  </span>
                </div>
              </div>
            </div>

            <div className="pt-4 border-t border-border-subtle text-center">
              <Link to="/skills" className="text-xs font-medium text-accent-violet hover:underline inline-flex items-center gap-1">
                <span>Inspect full taxonomy skill tree</span>
                <ArrowRight className="w-3 h-3" />
              </Link>
            </div>
          </Card>
        </div>

        {/* Active Enrolled Courses Section */}
        {enrolledCourses.length > 0 && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-text-primary">Enrolled Courses</h2>
                <p className="text-xs text-text-secondary">
                  Track your progress and access interactive lesson workspaces
                </p>
              </div>
              <span className="text-xs font-mono text-text-muted">
                {enrolledCourses.length} {enrolledCourses.length === 1 ? 'Course' : 'Courses'}
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {enrolledCourses.map((c) => (
                <Card key={c.id} variant="elevated" className="p-5 flex flex-col justify-between space-y-4 hover:border-accent-violet/40 transition-colors">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-[11px] font-mono text-text-muted">
                        Version {c.version_number}
                      </span>
                      <Badge
                        variant={c.status === 'COMPLETED' ? 'emerald' : c.status === 'IN_PROGRESS' ? 'violet' : 'cyan'}
                        size="sm"
                      >
                        {c.status}
                      </Badge>
                    </div>

                    <h3 className="text-base font-bold text-text-primary line-clamp-1">
                      {c.course_title}
                    </h3>
                    <p className="text-xs text-text-muted font-mono mt-1">
                      {c.lessons_completed} of {c.lessons_total} lessons completed
                    </p>
                  </div>

                  <div className="space-y-3 pt-2 border-t border-border-subtle">
                    <ProgressBar
                      value={c.progress_percentage}
                      variant={c.status === 'COMPLETED' ? 'emerald' : 'violet'}
                      size="sm"
                    />

                    <div className="flex items-center justify-between pt-1">
                      <Link to={`/courses/${c.course_slug}`} className="text-xs text-text-muted hover:text-text-primary">
                        Syllabus
                      </Link>
                      <Link to={`/learn/${c.course_slug}`}>
                        <Button variant="primary" size="sm" rightIcon={<ArrowRight className="w-3.5 h-3.5" />}>
                          {c.status === 'COMPLETED' ? 'Review' : 'Continue'}
                        </Button>
                      </Link>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* Recommendations & Recent Attempts Strip */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Next-Step Recommendations */}
          <Card variant="surface" className="p-5 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-text-primary flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-accent-violet" />
                <span>Next-Step Recommendations</span>
              </h3>
              <Badge variant="violet" size="sm">
                Deterministic
              </Badge>
            </div>

            {recommendations.length > 0 ? (
              <div className="space-y-3">
                {recommendations.map((rec, idx) => (
                  <div
                    key={idx}
                    className="p-3.5 rounded-xl bg-bg-base border border-border-subtle flex items-start justify-between gap-3"
                  >
                    <div className="space-y-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-accent-violet/10 text-accent-violet font-semibold">
                          {rec.type.replace('_', ' ')}
                        </span>
                        <h4 className="text-xs font-bold text-text-primary truncate">
                          {rec.title}
                        </h4>
                      </div>
                      <p className="text-[11px] text-text-secondary leading-snug">
                        {rec.reason}
                      </p>
                    </div>

                    {rec.course_slug && (
                      <Link to={`/courses/${rec.course_slug}`} className="shrink-0 self-center">
                        <Button variant="outline" size="sm" className="text-xs">
                          Go
                        </Button>
                      </Link>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-text-muted py-6 text-center">
                No new recommendations. Continue your current enrolled coursework!
              </p>
            )}
          </Card>

          {/* Recent Assessment Attempts */}
          <Card variant="surface" className="p-5 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-text-primary flex items-center gap-2">
                <Target className="w-4 h-4 text-accent-cyan" />
                <span>Recent Assessment Attempts</span>
              </h3>
              <span className="text-xs font-mono text-text-muted">
                {recentAttempts.length} logged
              </span>
            </div>

            {recentAttempts.length > 0 ? (
              <div className="space-y-2">
                {recentAttempts.slice(0, 5).map((att) => (
                  <div
                    key={att.attempt_id}
                    className="p-3 rounded-lg bg-bg-base border border-border-subtle flex items-center justify-between gap-3"
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      <div className="p-1.5 rounded-md bg-bg-surface shrink-0">
                        {getActivityTypeIcon(att.activity_type)}
                      </div>
                      <div className="min-w-0">
                        <p className="text-xs font-semibold text-text-primary truncate">
                          {att.activity_title}
                        </p>
                        <span className="text-[10px] font-mono text-text-muted">
                          Score: {att.score}/{att.max_score}
                        </span>
                      </div>
                    </div>

                    <Badge variant={att.passed ? 'emerald' : 'amber'} size="sm">
                      {att.passed ? 'Passed' : 'Needs Review'}
                    </Badge>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-text-muted py-6 text-center">
                No interactive submissions recorded yet. Open a lesson to practice!
              </p>
            )}
          </Card>
        </div>

        {/* Achievements Shelf */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-text-primary flex items-center gap-2">
                <Award className="w-5 h-5 text-state-warning" />
                <span>Achievements Shelf</span>
              </h2>
              <p className="text-xs text-text-secondary">
                Milestones unlocked through verified learning progress and assessment performance
              </p>
            </div>
            <span className="text-xs font-mono text-text-muted">
              {achievements.filter((a) => a.earned).length} of {achievements.length} Unlocked
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            {achievements.map((ach) => (
              <Card
                key={ach.id}
                variant={ach.earned ? 'elevated' : 'base'}
                className={`p-4 flex flex-col items-center text-center space-y-2 transition-all ${
                  ach.earned
                    ? 'border-state-warning/40 shadow-[0_0_15px_rgba(245,158,11,0.1)]'
                    : 'opacity-50 border-dashed border-border-subtle'
                }`}
              >
                <div
                  className={`w-12 h-12 rounded-full flex items-center justify-center ${
                    ach.earned
                      ? 'bg-state-warning/15 text-state-warning'
                      : 'bg-bg-surface text-text-muted'
                  }`}
                >
                  {ach.earned ? getAchievementIcon(ach.slug) : <Lock className="w-5 h-5" />}
                </div>

                <div className="space-y-0.5">
                  <h4 className="text-xs font-bold text-text-primary line-clamp-1">
                    {ach.name}
                  </h4>
                  <p className="text-[10px] text-text-muted line-clamp-2 leading-tight">
                    {ach.description}
                  </p>
                </div>

                {ach.earned ? (
                  <span className="text-[9px] font-mono text-state-success font-semibold uppercase tracking-wider">
                    Unlocked
                  </span>
                ) : (
                  <span className="text-[9px] font-mono text-text-muted uppercase tracking-wider">
                    Locked
                  </span>
                )}
              </Card>
            ))}
          </div>
        </div>
      </div>
    )
  }

  // 2. Fallback / Demonstration Preview (for logged-out visitors)
  const data = SAMPLE_DASHBOARD_DATA
  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Demo Banner */}
      <div className="flex items-center justify-between p-3.5 rounded-xl bg-accent-violet/10 border border-accent-violet/25 text-xs text-text-secondary">
        <div className="flex items-center gap-2.5">
          <Sparkles className="w-4 h-4 text-accent-violet shrink-0" />
          <span>
            <strong className="text-text-primary">Demonstration Preview:</strong> You are viewing sample data. Sign in to track your persistent learning progress and earn verified skill mastery.
          </span>
        </div>
        <Link to="/login">
          <Button variant="primary" size="sm">
            Sign In
          </Button>
        </Link>
      </div>

      {/* Hero / Welcome Area */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-text-primary tracking-tight">
            Welcome back, {data.learnerName}
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            Explore how SkillVerse tracks multi-tier mastery and course progress.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link to="/explore">
            <Button variant="outline" size="sm" leftIcon={<Compass className="w-4 h-4" />}>
              Explore Courses
            </Button>
          </Link>
          <Link to="/skills">
            <Button variant="primary" size="sm" rightIcon={<ArrowRight className="w-4 h-4" />}>
              View Skill Map
            </Button>
          </Link>
        </div>
      </div>

      {/* Top Grid: Continue Learning Hero & Weekly Goal */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card variant="elevated" className="lg:col-span-2 relative overflow-hidden flex flex-col justify-between p-6">
          <div className="absolute top-0 right-0 w-96 h-96 bg-accent-violet/5 rounded-full blur-3xl pointer-events-none" />

          <div>
            <div className="flex items-center justify-between mb-4">
              <Badge variant="cyan" size="sm" icon={<BookOpen className="w-3 h-3" />}>
                {data.continueItem.categoryName}
              </Badge>
              <span className="text-xs font-mono text-text-muted">
                Last active {data.continueItem.lastAccessed}
              </span>
            </div>

            <h2 className="text-xl font-bold text-text-primary mb-1">
              {data.continueItem.courseTitle}
            </h2>
            <p className="text-sm text-text-secondary mb-2">
              {data.continueItem.currentModuleTitle}
            </p>

            <div className="p-3.5 rounded-xl bg-bg-surface/60 border border-border-subtle mb-6">
              <div className="flex items-center gap-2 text-xs font-medium text-text-primary mb-1">
                <Code className="w-3.5 h-3.5 text-accent-violet" />
                <span>Next Lesson: {data.continueItem.currentLessonTitle}</span>
              </div>
              <p className="text-xs text-text-muted">
                Code exercise • Estimated 25 minutes • Build accessible label associations and client constraints.
              </p>
            </div>
          </div>

          <div className="space-y-4 pt-2 border-t border-border-subtle">
            <ProgressBar
              value={data.continueItem.progressPct}
              label="Course Completion Progress"
              showPercentage
              variant="cyan"
              size="md"
            />

            <div className="flex items-center justify-between pt-1">
              <span className="text-xs text-text-muted">
                Module 1 of 3 in progress
              </span>
              <Link to={`/courses/${data.continueItem.courseSlug}`}>
                <Button variant="primary" size="md" leftIcon={<Play className="w-4 h-4 fill-current" />}>
                  Resume Learning
                </Button>
              </Link>
            </div>
          </div>
        </Card>

        <Card variant="surface" className="flex flex-col justify-between p-6">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold uppercase tracking-wider text-text-muted flex items-center gap-2">
                <Target className="w-4 h-4 text-accent-violet" />
                <span>Weekly Goal</span>
              </h3>
              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-state-warning/10 text-state-warning border border-state-warning/25 text-xs font-semibold">
                <Flame className="w-3.5 h-3.5 fill-current" />
                <span>{data.weeklyGoal.streakDays}-Day Streak</span>
              </div>
            </div>

            <div className="text-center py-4">
              <div className="text-4xl font-extrabold text-text-primary tracking-tight font-mono">
                {data.weeklyGoal.completedSessions}
                <span className="text-text-muted text-2xl font-normal"> / {data.weeklyGoal.targetSessions}</span>
              </div>
              <p className="text-xs text-text-secondary mt-1">
                Interactive sessions completed this week
              </p>
            </div>
          </div>

          <div className="pt-4 border-t border-border-subtle text-xs text-text-secondary text-center">
            Log in to record persistent streaks and verified session achievements.
          </div>
        </Card>
      </div>

      {/* Stats Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <Card variant="base" className="p-4 flex flex-col justify-center">
          <div className="text-xs font-medium text-text-muted mb-1 flex items-center gap-1.5">
            <BookOpen className="w-3.5 h-3.5 text-accent-violet" />
            <span>Enrolled Courses</span>
          </div>
          <div className="text-2xl font-bold font-mono text-text-primary">
            {data.summary.coursesInProgress}
          </div>
          <div className="text-[11px] text-text-muted mt-1">2 in tech, 1 in comms</div>
        </Card>

        <Card variant="base" className="p-4 flex flex-col justify-center">
          <div className="text-xs font-medium text-text-muted mb-1 flex items-center gap-1.5">
            <TrendingUp className="w-3.5 h-3.5 text-accent-cyan" />
            <span>Skills Practicing</span>
          </div>
          <div className="text-2xl font-bold font-mono text-text-primary">
            {data.summary.skillsPracticing}
          </div>
          <div className="text-[11px] text-text-muted mt-1">Across 3 disciplines</div>
        </Card>

        <Card variant="base" className="p-4 flex flex-col justify-center">
          <div className="text-xs font-medium text-text-muted mb-1 flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-state-success" />
            <span>Exercises Completed</span>
          </div>
          <div className="text-2xl font-bold font-mono text-text-primary">
            {data.summary.activitiesCompleted}
          </div>
          <div className="text-[11px] text-text-muted mt-1">Code, quizzes & tasks</div>
        </Card>

        <Card variant="base" className="p-4 flex flex-col justify-center">
          <div className="text-xs font-medium text-text-muted mb-1 flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-state-warning" />
            <span>Hours Practiced</span>
          </div>
          <div className="text-2xl font-bold font-mono text-text-primary">
            {data.summary.estimatedHoursLearned}h
          </div>
          <div className="text-[11px] text-text-muted mt-1">Active workspace time</div>
        </Card>
      </div>

      {/* Cross-Disciplinary Platform Vision Callout */}
      <Card variant="elevated" className="border-accent-violet/30 bg-gradient-to-r from-bg-elevated via-bg-surface/80 to-bg-elevated p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2 max-w-2xl">
            <Badge variant="violet" size="sm">
              The SkillVerse Approach
            </Badge>
            <h2 className="text-xl font-bold text-text-primary">
              Learn by Doing Across Multiple Disciplines
            </h2>
            <p className="text-sm text-text-secondary leading-relaxed">
              Traditional courses rely on passive video streams. SkillVerse structures every skill around chapter-based practice, live execution sandboxes, and immediate feedback loops.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 shrink-0">
            <div className="p-3 rounded-lg bg-bg-base/80 border border-border-subtle flex items-center gap-2.5">
              <Code className="w-4 h-4 text-accent-violet shrink-0" />
              <div className="text-xs">
                <p className="font-semibold text-text-primary">Code Sandbox</p>
                <p className="text-[10px] text-text-muted">Automated verification</p>
              </div>
            </div>

            <div className="p-3 rounded-lg bg-bg-base/80 border border-border-subtle flex items-center gap-2.5">
              <BookOpen className="w-4 h-4 text-accent-cyan shrink-0" />
              <div className="text-xs">
                <p className="font-semibold text-text-primary">Simulations</p>
                <p className="text-[10px] text-text-muted">Workplace role-play</p>
              </div>
            </div>

            <div className="p-3 rounded-lg bg-bg-base/80 border border-border-subtle flex items-center gap-2.5">
              <ShieldCheck className="w-4 h-4 text-state-success shrink-0" />
              <div className="text-xs">
                <p className="font-semibold text-text-primary">Frameworks</p>
                <p className="text-[10px] text-text-muted">First-principles thinking</p>
              </div>
            </div>
          </div>
        </div>
      </Card>
    </div>
  )
}
