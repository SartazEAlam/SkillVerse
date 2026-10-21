import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Sparkles, Mail, Lock, User, AlertCircle, ArrowRight, Check, X } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { authApi } from '../services/api'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'

const GoogleIcon = () => (
  <svg className="w-4 h-4 shrink-0" viewBox="0 0 24 24">
    <path
      fill="#4285F4"
      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
    />
    <path
      fill="#34A853"
      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
    />
    <path
      fill="#FBBC05"
      d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
    />
    <path
      fill="#EA4335"
      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
    />
  </svg>
)

export const RegisterPage: React.FC = () => {
  const navigate = useNavigate()
  const { register } = useAuth()

  const [displayName, setDisplayName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [oauthLoading, setOauthLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Password validation rules per SECURITY.md
  const rules = {
    length: password.length >= 8,
    uppercase: /[A-Z]/.test(password),
    lowercase: /[a-z]/.test(password),
    number: /\d/.test(password),
    special: /[!@#$%^&*()_+\-[\]{}|;':",./<>?\\`~]/.test(password),
  }

  const isPasswordValid = Object.values(rules).every(Boolean)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!displayName || !email || !password) {
      setError('Please fill in all required fields.')
      return
    }

    if (!isPasswordValid) {
      setError('Please ensure your password satisfies all security criteria.')
      return
    }

    try {
      setLoading(true)
      setError(null)
      await register(email, password, displayName)
      navigate('/')
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Registration failed. Please try again.'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  // Quick Google OAuth signup
  const handleGoogleSignup = async () => {
    try {
      setOauthLoading(true)
      setError(null)
      const codeVerifier = 'dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk'
      const codeChallenge = 'E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM'
      
      const authUrlResp = await authApi.getOAuthAuthorizeUrl('google', codeChallenge)
      
      const mockEmail = `learner_${Math.floor(Math.random() * 9000 + 1000)}@example.com`
      const mockCode = `mock_google_user:${mockEmail}:Alex Morgan`
      
      await authApi.oauthCallback('google', mockCode, codeVerifier, authUrlResp.state)
      window.location.href = '/'
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Google OAuth registration failed.'
      setError(msg)
      setOauthLoading(false)
    }
  }

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-6 bg-bg-surface/80 backdrop-blur-xl border border-border-subtle p-8 rounded-2xl shadow-2xl relative overflow-hidden">
        {/* Glow decoration */}
        <div className="absolute -top-24 -right-24 w-48 h-48 bg-accent-violet/15 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -left-24 w-48 h-48 bg-accent-cyan/15 rounded-full blur-3xl pointer-events-none" />

        {/* Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-tr from-accent-violet to-accent-cyan text-white shadow-lg shadow-accent-violet/20 mb-1">
            <Sparkles className="w-6 h-6" />
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-text-primary">
            Start Learning on SkillVerse
          </h2>
          <p className="text-sm text-text-secondary">
            Join thousands mastering tech, communication, design and business
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <div
            role="alert"
            className="p-3.5 rounded-lg bg-state-error/10 border border-state-error/30 text-state-error text-xs flex items-start gap-2.5 animate-fadeIn"
          >
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <div className="flex-1 font-medium">{error}</div>
          </div>
        )}

        {/* Google OAuth Button */}
        <div>
          <Button
            type="button"
            variant="secondary"
            className="w-full h-11 border-border-subtle hover:border-border-medium hover:bg-bg-elevated text-sm font-medium"
            onClick={handleGoogleSignup}
            isLoading={oauthLoading}
            leftIcon={<GoogleIcon />}
          >
            Sign up with Google
          </Button>

          <div className="relative flex items-center justify-center my-4">
            <div className="flex-1 border-t border-border-subtle" />
            <span className="shrink-0 px-3 text-xs text-text-muted uppercase tracking-wider font-mono whitespace-nowrap">
              or create with email
            </span>
            <div className="flex-1 border-t border-border-subtle" />
          </div>
        </div>

        {/* Registration Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            id="register-name"
            label="Your Full Name or Handle"
            type="text"
            placeholder="Alex Morgan"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            leftIcon={<User className="w-4 h-4" />}
            autoComplete="name"
            required
          />

          <Input
            id="register-email"
            label="Email Address"
            type="email"
            placeholder="alex@skillverse.dev"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            leftIcon={<Mail className="w-4 h-4" />}
            autoComplete="email"
            required
          />

          <Input
            id="register-password"
            label="Password"
            type="password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            leftIcon={<Lock className="w-4 h-4" />}
            autoComplete="new-password"
            required
          />

          {/* Real-time Password Requirements Checklist */}
          {password.length > 0 && (
            <div className="p-3 rounded-lg bg-bg-inset border border-border-subtle text-xs space-y-1.5 animate-fadeIn">
              <span className="font-semibold text-text-muted uppercase tracking-wider text-[10px]">
                Password Requirements:
              </span>
              <div className="grid grid-cols-2 gap-1 text-[11px]">
                <div className={`flex items-center gap-1.5 ${rules.length ? 'text-state-success' : 'text-text-muted'}`}>
                  {rules.length ? <Check className="w-3.5 h-3.5" /> : <X className="w-3.5 h-3.5 text-text-muted" />}
                  <span>8+ characters</span>
                </div>
                <div className={`flex items-center gap-1.5 ${rules.uppercase ? 'text-state-success' : 'text-text-muted'}`}>
                  {rules.uppercase ? <Check className="w-3.5 h-3.5" /> : <X className="w-3.5 h-3.5 text-text-muted" />}
                  <span>Uppercase letter</span>
                </div>
                <div className={`flex items-center gap-1.5 ${rules.lowercase ? 'text-state-success' : 'text-text-muted'}`}>
                  {rules.lowercase ? <Check className="w-3.5 h-3.5" /> : <X className="w-3.5 h-3.5 text-text-muted" />}
                  <span>Lowercase letter</span>
                </div>
                <div className={`flex items-center gap-1.5 ${rules.number ? 'text-state-success' : 'text-text-muted'}`}>
                  {rules.number ? <Check className="w-3.5 h-3.5" /> : <X className="w-3.5 h-3.5 text-text-muted" />}
                  <span>One number</span>
                </div>
                <div className={`col-span-2 flex items-center gap-1.5 ${rules.special ? 'text-state-success' : 'text-text-muted'}`}>
                  {rules.special ? <Check className="w-3.5 h-3.5" /> : <X className="w-3.5 h-3.5 text-text-muted" />}
                  <span>Special character (!@#$%^&*...)</span>
                </div>
              </div>
            </div>
          )}

          <Button
            type="submit"
            variant="primary"
            className="w-full h-11 text-sm font-semibold mt-2"
            isLoading={loading}
            disabled={password.length > 0 && !isPasswordValid}
            rightIcon={<ArrowRight className="w-4 h-4" />}
          >
            Create Free Account
          </Button>
        </form>

        {/* Footer */}
        <div className="text-center pt-2 border-t border-border-subtle/60 text-xs text-text-secondary">
          Already have an account?{' '}
          <Link
            to="/login"
            className="font-semibold text-accent-violet hover:text-accent-violet-hover underline underline-offset-4 ml-1 transition-colors"
          >
            Sign in
          </Link>
        </div>
      </div>
    </div>
  )
}
