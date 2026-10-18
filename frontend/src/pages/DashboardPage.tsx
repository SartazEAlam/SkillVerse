import React from 'react'
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
  MessageSquare,
  Compass,
  CheckCircle2,
  Terminal,
  ShieldCheck,
  TrendingUp
} from 'lucide-react'
import { SAMPLE_DASHBOARD_DATA } from '../data/dashboard'
import { SAMPLE_COURSES } from '../data/courses'
import { Card } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { ProgressBar } from '../components/ui/ProgressBar'

export const DashboardPage: React.FC = () => {
  const data = SAMPLE_DASHBOARD_DATA
  const recommendedCourses = SAMPLE_COURSES.slice(1, 4)

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Demo Banner */}
      <div className="flex items-center justify-between p-3.5 rounded-xl bg-accent-violet/10 border border-accent-violet/25 text-xs text-text-secondary">
        <div className="flex items-center gap-2.5">
          <Sparkles className="w-4 h-4 text-accent-violet shrink-0" />
          <span>
            <strong className="text-text-primary">Phase 1 Preview Mode:</strong> This dashboard is populated with realistic demonstration data for <strong className="text-text-primary">{data.learnerName}</strong>.
          </span>
        </div>
        <Badge variant="violet" size="sm">
          Sample Data
        </Badge>
      </div>

      {/* Hero / Welcome Area */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-text-primary tracking-tight">
            Welcome back, {data.learnerName}
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            Pick up right where you left off. Today is an ideal day to sharpen your core web structure skills.
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
        {/* Continue Learning Card (2 cols) */}
        <Card variant="elevated" className="lg:col-span-2 relative overflow-hidden flex flex-col justify-between">
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

        {/* Weekly Goal & Streak Card (1 col) */}
        <Card variant="surface" className="flex flex-col justify-between">
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

            {/* Session Indicator Dots */}
            <div className="grid grid-cols-5 gap-2 my-4">
              {Array.from({ length: data.weeklyGoal.targetSessions }).map((_, index) => {
                const isCompleted = index < data.weeklyGoal.completedSessions
                return (
                  <div
                    key={index}
                    className={`h-9 rounded-lg flex items-center justify-center border text-xs font-mono font-medium transition-all ${
                      isCompleted
                        ? 'bg-accent-violet/20 border-accent-violet text-accent-violet'
                        : 'bg-bg-inset border-border-subtle text-text-muted'
                    }`}
                    title={isCompleted ? `Session ${index + 1}: Completed` : `Session ${index + 1}: Pending`}
                  >
                    {isCompleted ? <CheckCircle2 className="w-4 h-4" /> : `S${index + 1}`}
                  </div>
                )
              })}
            </div>
          </div>

          <div className="pt-4 border-t border-border-subtle text-xs text-text-secondary text-center">
            2 more interactive sessions to hit your target before Sunday.
          </div>
        </Card>
      </div>

      {/* Stats Summary Strip */}
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
      <Card variant="elevated" className="border-accent-violet/30 bg-gradient-to-r from-bg-elevated via-bg-surface/80 to-bg-elevated">
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
              <Terminal className="w-4 h-4 text-accent-violet shrink-0" />
              <div className="text-xs">
                <p className="font-semibold text-text-primary">Code Sandbox</p>
                <p className="text-[10px] text-text-muted">Automated verification</p>
              </div>
            </div>

            <div className="p-3 rounded-lg bg-bg-base/80 border border-border-subtle flex items-center gap-2.5">
              <MessageSquare className="w-4 h-4 text-accent-cyan shrink-0" />
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

      {/* Two Column Layout: Recommended Courses & Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recommended Courses (2 cols) */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-text-primary">Recommended Courses</h2>
              <p className="text-xs text-text-secondary">Explore complementary skills to broaden your portfolio</p>
            </div>
            <Link to="/explore" className="text-xs font-medium text-accent-violet hover:underline flex items-center gap-1">
              <span>View all 5 courses</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {recommendedCourses.map((course) => (
              <Card key={course.id} variant="elevated" hoverEffect className="flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <Badge variant="cyan" size="sm">
                      {course.categoryName}
                    </Badge>
                    <span className="text-xs font-mono text-text-muted">{course.estimatedHours}h total</span>
                  </div>
                  <h3 className="text-base font-semibold text-text-primary mb-1">
                    {course.title}
                  </h3>
                  <p className="text-xs text-text-secondary line-clamp-2 mb-4">
                    {course.shortDescription}
                  </p>
                </div>

                <div className="pt-3 border-t border-border-subtle flex items-center justify-between">
                  <span className="text-xs text-text-muted font-medium">
                    {course.modulesCount} modules • {course.lessonsCount} lessons
                  </span>
                  <Link to={`/courses/${course.slug}`}>
                    <Button variant="outline" size="sm">
                      Overview
                    </Button>
                  </Link>
                </div>
              </Card>
            ))}
          </div>
        </div>

        {/* Recent Activity Log (1 col) */}
        <div className="space-y-4">
          <div>
            <h2 className="text-lg font-bold text-text-primary">Recent Practice</h2>
            <p className="text-xs text-text-secondary">Sample activity verification history</p>
          </div>

          <Card variant="surface" className="p-0 overflow-hidden">
            <div className="divide-y divide-border-subtle">
              {data.recentActivities.map((act) => (
                <div key={act.id} className="p-4 hover:bg-bg-elevated/40 transition-colors">
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-xs font-semibold text-text-primary">
                      {act.title}
                    </p>
                    {act.score !== undefined && (
                      <span className="text-xs font-mono font-bold text-state-success">
                        {act.score}%
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-text-muted mt-0.5 truncate">
                    {act.courseTitle}
                  </p>
                  <p className="text-[10px] text-text-muted font-mono mt-1">
                    {act.timestamp}
                  </p>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
