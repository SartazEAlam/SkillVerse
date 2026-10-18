export interface WeeklyGoal {
  targetSessions: number
  completedSessions: number
  streakDays: number
}

export interface ProgressSummary {
  coursesInProgress: number
  skillsPracticing: number
  activitiesCompleted: number
  estimatedHoursLearned: number
}

export interface ContinueLearningItem {
  courseId: string
  courseSlug: string
  courseTitle: string
  categoryName: string
  currentModuleTitle: string
  currentLessonTitle: string
  progressPct: number
  lastAccessed: string
}

export interface RecentActivityItem {
  id: string
  type: 'code_exercise' | 'conversation' | 'quiz' | 'practical_task'
  title: string
  courseTitle: string
  timestamp: string
  score?: number
}

export interface DashboardData {
  learnerName: string
  isDemoData: boolean
  weeklyGoal: WeeklyGoal
  summary: ProgressSummary
  continueItem: ContinueLearningItem
  recentActivities: RecentActivityItem[]
}
