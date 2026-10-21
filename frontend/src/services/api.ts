import type {
  AuthResponse,
  DeleteAccountResponse,
  MessageResponse,
  OAuthAuthorizeResponse,
  RegisterResponse,
  User,
} from '../types/auth'

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1'

const ACCESS_TOKEN_KEY = 'skillverse_access_token'
const REFRESH_TOKEN_KEY = 'skillverse_refresh_token'

export class ApiError extends Error {
  code: string
  status: number
  details?: unknown

  constructor(message: string, code = 'API_ERROR', status = 400, details?: unknown) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.status = status
    this.details = details
  }
}

export const tokenStorage = {
  getAccessToken: () => localStorage.getItem(ACCESS_TOKEN_KEY),
  getRefreshToken: () => localStorage.getItem(REFRESH_TOKEN_KEY),
  setTokens: (accessToken: string, refreshToken: string) => {
    localStorage.setItem(ACCESS_TOKEN_KEY, accessToken)
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken)
  },
  clearTokens: () => {
    localStorage.removeItem(ACCESS_TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
  },
}

let isRefreshing = false
let refreshSubscribers: ((token: string) => void)[] = []

function subscribeTokenRefresh(cb: (token: string) => void) {
  refreshSubscribers.push(cb)
}

function onRefreshed(token: string) {
  refreshSubscribers.forEach((cb) => cb(token))
  refreshSubscribers = []
}

export async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${endpoint}`
  const headers = new Headers(options.headers || {})

  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
  }

  const token = tokenStorage.getAccessToken()
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  let response = await fetch(url, { ...options, headers })

  // Handle 401 Unauthorized -> Attempt token refresh
  if (response.status === 401 && tokenStorage.getRefreshToken() && !endpoint.includes('/auth/refresh') && !endpoint.includes('/auth/login')) {
    if (!isRefreshing) {
      isRefreshing = true
      try {
        const refreshResp = await fetch(`${API_BASE}/auth/refresh`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: tokenStorage.getRefreshToken() }),
        })

        if (refreshResp.ok) {
          const authData: AuthResponse = await refreshResp.json()
          tokenStorage.setTokens(authData.access_token, authData.refresh_token)
          isRefreshing = false
          onRefreshed(authData.access_token)
        } else {
          isRefreshing = false
          tokenStorage.clearTokens()
          window.dispatchEvent(new Event('auth:unauthorized'))
          throw new ApiError('Session expired. Please log in again.', 'UNAUTHORIZED', 401)
        }
      } catch (err) {
        isRefreshing = false
        tokenStorage.clearTokens()
        window.dispatchEvent(new Event('auth:unauthorized'))
        throw err
      }
    }

    // Wait for the new token and retry
    const retryPromise = new Promise<T>((resolve, reject) => {
      subscribeTokenRefresh((newToken) => {
        headers.set('Authorization', `Bearer ${newToken}`)
        fetch(url, { ...options, headers })
          .then((res) => res.json())
          .then(resolve)
          .catch(reject)
      })
    })

    return retryPromise
  }

  // Parse response
  const contentType = response.headers.get('content-type')
  const isJson = contentType && contentType.includes('application/json')
  const data = isJson ? await response.json() : null

  if (!response.ok) {
    const errorPayload = data?.error || data?.detail?.error || data?.detail
    const message =
      (typeof errorPayload === 'object' ? errorPayload?.message : errorPayload) ||
      response.statusText ||
      'Request failed'
    const code = errorPayload?.code || (response.status === 429 ? 'RATE_LIMITED' : 'HTTP_ERROR')
    throw new ApiError(message, code, response.status, errorPayload?.details)
  }

  return data as T
}

// ── Auth Service API Calls ──────────────────────────

export const authApi = {
  async register(body: { email: string; password: string; display_name: string }): Promise<RegisterResponse> {
    return request<RegisterResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(body),
    })
  },

  async login(body: { email: string; password: string }): Promise<AuthResponse> {
    const data = await request<AuthResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(body),
    })
    tokenStorage.setTokens(data.access_token, data.refresh_token)
    return data
  },

  async logout(): Promise<MessageResponse> {
    try {
      const resp = await request<MessageResponse>('/auth/logout', { method: 'POST' })
      return resp
    } finally {
      tokenStorage.clearTokens()
    }
  },

  async getMe(): Promise<User> {
    return request<User>('/users/me')
  },

  async updateMe(body: { display_name?: string; bio?: string; timezone?: string; avatar_url?: string }): Promise<User> {
    return request<User>('/users/me', {
      method: 'PATCH',
      body: JSON.stringify(body),
    })
  },

  async updatePreferences(preferences: Record<string, unknown>): Promise<User> {
    return request<User>('/users/me/preferences', {
      method: 'PATCH',
      body: JSON.stringify(preferences),
    })
  },

  async exportData(): Promise<Record<string, unknown>> {
    return request<Record<string, unknown>>('/users/me/export')
  },

  async deleteAccount(password: string): Promise<DeleteAccountResponse> {
    const resp = await request<DeleteAccountResponse>('/users/me', {
      method: 'DELETE',
      body: JSON.stringify({ password }),
    })
    tokenStorage.clearTokens()
    return resp
  },

  async getOAuthAuthorizeUrl(provider = 'google', codeChallenge: string): Promise<OAuthAuthorizeResponse> {
    const params = new URLSearchParams({
      code_challenge: codeChallenge,
      code_challenge_method: 'S256',
    })
    return request<OAuthAuthorizeResponse>(`/auth/oauth/${provider}/authorize?${params.toString()}`)
  },

  async oauthCallback(
    provider = 'google',
    code: string,
    codeVerifier: string,
    state: string
  ): Promise<AuthResponse> {
    const data = await request<AuthResponse>(`/auth/oauth/${provider}/callback`, {
      method: 'POST',
      body: JSON.stringify({ code, code_verifier: codeVerifier, state }),
    })
    tokenStorage.setTokens(data.access_token, data.refresh_token)
    return data
  },
}
