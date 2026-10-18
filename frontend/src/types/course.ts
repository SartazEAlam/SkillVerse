export type CourseLevel = 'Beginner' | 'Intermediate' | 'Advanced'

export type ActivityType =
  | 'code_exercise'
  | 'conversation'
  | 'quiz'
  | 'practical_task'
  | 'reading'

export interface LessonSummary {
  id: string
  slug: string
  title: string
  estimatedMinutes: number
  activityType: ActivityType
  description: string
}

export interface CourseModule {
  id: string
  title: string
  description: string
  sortOrder: number
  lessons: LessonSummary[]
}

export interface Course {
  id: string
  slug: string
  title: string
  shortDescription: string
  fullDescription: string
  categoryId: string
  categoryName: string
  level: CourseLevel
  estimatedHours: number
  modulesCount: number
  lessonsCount: number
  skillsTaught: string[]
  learningObjectives: string[]
  modules: CourseModule[]
}
