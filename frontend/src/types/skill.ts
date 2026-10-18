export type SkillLevel = 'Foundational' | 'Intermediate' | 'Advanced'

export interface SkillCategory {
  id: string
  name: string
  description: string
  color: string
}

export interface Skill {
  id: string
  slug: string
  name: string
  categoryId: string
  level: SkillLevel
  description: string
  prerequisites: string[] // IDs of prerequisite skills
  unlockedSkills: string[] // IDs of skills this unlocks
  courseSlugs: string[] // Associated courses
  sampleMasteryPct: number // Explicitly marked as demo data
  x?: number // Graph visual coordinates (0 - 100 percentage)
  y?: number
}
