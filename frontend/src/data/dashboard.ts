import type { DashboardData } from '../types/dashboard'

export const SAMPLE_DASHBOARD_DATA: DashboardData = {
  learnerName: 'Alex Morgan',
  isDemoData: true,
  weeklyGoal: {
    targetSessions: 5,
    completedSessions: 3,
    streakDays: 4
  },
  summary: {
    coursesInProgress: 3,
    skillsPracticing: 7,
    activitiesCompleted: 14,
    estimatedHoursLearned: 6.5
  },
  continueItem: {
    courseId: 'course-web-dev',
    courseSlug: 'web-dev-foundations',
    courseTitle: 'Web Development Foundations',
    categoryName: 'Programming & Web',
    currentModuleTitle: 'Module 1: Semantic HTML & Document Architecture',
    currentLessonTitle: 'Accessible Forms & Client-Side Validation',
    progressPct: 45,
    lastAccessed: '2 hours ago'
  },
  recentActivities: [
    {
      id: 'act-1',
      type: 'code_exercise',
      title: 'Semantic Structure Challenge',
      courseTitle: 'Web Development Foundations',
      timestamp: 'Today, 2:15 PM',
      score: 100
    },
    {
      id: 'act-2',
      type: 'conversation',
      title: '90-Second Daily Standup Simulation',
      courseTitle: 'Spoken English and Professional Communication',
      timestamp: 'Yesterday, 6:40 PM',
      score: 88
    },
    {
      id: 'act-3',
      type: 'practical_task',
      title: 'Priority Quadrant Matrix Audit',
      courseTitle: 'Personal Productivity and Systems Thinking',
      timestamp: '2 days ago',
      score: 92
    },
    {
      id: 'act-4',
      type: 'quiz',
      title: 'HTML & ARIA Landmark Roles',
      courseTitle: 'Web Development Foundations',
      timestamp: '3 days ago',
      score: 95
    }
  ]
}
