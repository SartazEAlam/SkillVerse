import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { LoginPage } from '../pages/LoginPage'
import { RegisterPage } from '../pages/RegisterPage'
import { ProfilePage } from '../pages/ProfilePage'
import { AuthProvider } from '../context/AuthContext'

describe('Authentication & Profile Pages', () => {
  it('renders LoginPage with credentials form and Google OAuth button', () => {
    render(
      <BrowserRouter>
        <AuthProvider>
          <LoginPage />
        </AuthProvider>
      </BrowserRouter>
    )

    expect(screen.getByText(/Welcome back to SkillVerse/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Email Address/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Sign In/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Continue with Google/i })).toBeInTheDocument()
  })

  it('renders RegisterPage with registration form and password requirements', () => {
    render(
      <BrowserRouter>
        <AuthProvider>
          <RegisterPage />
        </AuthProvider>
      </BrowserRouter>
    )

    expect(screen.getByText(/Start Learning on SkillVerse/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Your Full Name or Handle/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Email Address/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Create Free Account/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Sign up with Google/i })).toBeInTheDocument()
  })

  it('renders ProfilePage prompt when unauthenticated', () => {
    render(
      <BrowserRouter>
        <AuthProvider>
          <ProfilePage />
        </AuthProvider>
      </BrowserRouter>
    )

    expect(screen.getByText(/Sign in to view your profile/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Log In/i })).toBeInTheDocument()
  })
})
