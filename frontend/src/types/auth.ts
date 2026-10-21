export type UserRole = 'learner' | 'creator' | 'admin'

export interface User {
  id: string
  email: string
  role: UserRole
  email_verified: boolean
  display_name: string | null
  avatar_url?: string | null
  bio?: string | null
  timezone?: string | null
  created_at: string
}

export interface UserPreferences {
  theme?: string
  reduced_motion?: boolean
  language?: string
}

export interface AuthResponse {
  access_token: string
  refresh_token: string
  expires_in: number
  user: User
}

export interface RegisterResponse {
  user: User
}

export interface MessageResponse {
  message: string
}

export interface DeleteAccountResponse {
  status: string
  grace_period_days: number
  scheduled_deletion_at: string
  message: string
}

export interface OAuthAuthorizeResponse {
  authorization_url: string
  state: string
}
