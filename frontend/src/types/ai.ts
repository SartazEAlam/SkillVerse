/**
 * TypeScript interfaces and contracts for Phase 8 AI Tutoring, Hints, and Preferences.
 */

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  suggestions?: string[]
  timestamp: string
}

export interface AITutorRequest {
  lesson_id: string
  message: string
  conversation_history?: Array<{
    role: 'user' | 'assistant'
    content: string
  }>
}

export interface AITutorResponse {
  reply?: string
  response?: string
  suggestions: string[]
  lesson_title?: string
  provider: string
  model?: string
  tokens_used?: number
}

export interface ActivityHintRequest {
  activity_id: string
  hint_level: number
}

export interface ActivityHintResponse {
  hint: string
  hint_level: number
  provider: string
}

export interface AIStatusResponse {
  enabled: boolean
  provider: string
  model: string
  opted_out: boolean
}

export interface AIPeriodicPreferenceRequest {
  opt_out: boolean
}

