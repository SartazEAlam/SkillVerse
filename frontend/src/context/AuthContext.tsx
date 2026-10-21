import React, { createContext, useContext, useEffect, useState } from 'react'
import { authApi, tokenStorage } from '../services/api'
import type { User } from '../types/auth'

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, displayName: string) => Promise<void>
  logout: () => Promise<void>
  updateProfile: (data: { display_name?: string; bio?: string; timezone?: string; avatar_url?: string }) => Promise<void>
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  const refreshUser = async () => {
    try {
      if (tokenStorage.getAccessToken()) {
        const currentUser = await authApi.getMe()
        setUser(currentUser)
      } else {
        setUser(null)
      }
    } catch {
      setUser(null)
      tokenStorage.clearTokens()
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    refreshUser()

    const handleUnauthorized = () => {
      setUser(null)
    }

    window.addEventListener('auth:unauthorized', handleUnauthorized)
    return () => window.removeEventListener('auth:unauthorized', handleUnauthorized)
  }, [])

  const login = async (email: string, password: string) => {
    const resp = await authApi.login({ email, password })
    setUser(resp.user)
  }

  const register = async (email: string, password: string, displayName: string) => {
    await authApi.register({ email, password, display_name: displayName })
    // Automatically log in after registration
    await login(email, password)
  }

  const logout = async () => {
    try {
      await authApi.logout()
    } finally {
      setUser(null)
    }
  }

  const updateProfile = async (data: { display_name?: string; bio?: string; timezone?: string; avatar_url?: string }) => {
    const updated = await authApi.updateMe(data)
    setUser(updated)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        register,
        logout,
        updateProfile,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext)
  if (!context) {
    return {
      user: null,
      loading: false,
      login: async () => {},
      register: async () => {},
      logout: async () => {},
      updateProfile: async () => {},
      refreshUser: async () => {},
    }
  }
  return context
}
