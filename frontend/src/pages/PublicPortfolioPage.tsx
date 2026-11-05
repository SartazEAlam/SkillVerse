import React, { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  Lock,
  AlertCircle,
  Loader2,
  ArrowLeft,
  Compass,
} from 'lucide-react'
import type { PortfolioPublic } from '../types/portfolio'
import { portfolioApi } from '../services/portfolioApi'
import { PublicPortfolioShowcase } from '../features/portfolio/PublicPortfolioShowcase'
import { ApiError } from '../services/api'

export const PublicPortfolioPage: React.FC = () => {
  const { slugOrId } = useParams<{ slugOrId: string }>()

  const [portfolio, setPortfolio] = useState<PortfolioPublic | null>(null)
  const [loading, setLoading] = useState(true)
  const [errorStatus, setErrorStatus] = useState<number | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  useEffect(() => {
    if (!slugOrId) return

    let mounted = true
    setLoading(true)
    setErrorStatus(null)
    setErrorMessage(null)

    portfolioApi
      .getPublicPortfolio(slugOrId)
      .then((res) => {
        if (mounted) setPortfolio(res)
      })
      .catch((err: unknown) => {
        if (mounted) {
          if (err instanceof ApiError) {
            setErrorStatus(err.status)
            setErrorMessage(err.message)
          } else {
            setErrorStatus(500)
            setErrorMessage('Unable to load portfolio.')
          }
        }
      })
      .finally(() => {
        if (mounted) setLoading(false)
      })

    return () => {
      mounted = false
    }
  }, [slugOrId])

  if (loading) {
    return (
      <main className="min-h-screen bg-bg-base py-16 px-4 sm:px-6 lg:px-8 max-w-4xl mx-auto flex flex-col items-center justify-center space-y-4">
        <Loader2 className="h-8 w-8 animate-spin text-accent-cyan" aria-hidden="true" />
        <p className="text-sm text-text-muted">Loading learner showcase...</p>
      </main>
    )
  }

  // Handle Private Portfolio (403 Forbidden or private message)
  if (errorStatus === 403 || errorMessage?.toLowerCase().includes('private')) {
    return (
      <main className="min-h-screen bg-bg-base py-16 px-4 sm:px-6 lg:px-8 max-w-xl mx-auto text-center space-y-6">
        <div className="inline-flex rounded-2xl bg-bg-surface p-6 text-text-muted border border-border-subtle shadow-lg">
          <Lock className="h-10 w-10 text-accent-violet" aria-hidden="true" />
        </div>
        <div className="space-y-2">
          <h1 className="text-2xl font-bold tracking-tight text-text-primary">
            This Portfolio is Private
          </h1>
          <p className="text-sm text-text-secondary leading-relaxed max-w-md mx-auto">
            The owner has set their portfolio visibility to Private. Only the portfolio owner can view this content.
          </p>
        </div>
        <div className="pt-2">
          <Link
            to="/explore"
            className="inline-flex items-center gap-2 rounded-lg bg-bg-surface border border-border-subtle px-4 py-2 text-xs font-semibold text-text-primary hover:bg-bg-elevated transition-colors"
          >
            <Compass className="h-4 w-4" aria-hidden="true" />
            <span>Explore SkillVerse Courses</span>
          </Link>
        </div>
      </main>
    )
  }

  // Handle 404 or Generic Error
  if (errorStatus === 404 || !portfolio) {
    return (
      <main className="min-h-screen bg-bg-base py-16 px-4 sm:px-6 lg:px-8 max-w-xl mx-auto text-center space-y-6">
        <div className="inline-flex rounded-2xl bg-state-error/10 p-6 text-state-error border border-state-error/20 shadow-lg">
          <AlertCircle className="h-10 w-10" aria-hidden="true" />
        </div>
        <div className="space-y-2">
          <h1 className="text-2xl font-bold tracking-tight text-text-primary">
            Portfolio Not Found
          </h1>
          <p className="text-sm text-text-secondary leading-relaxed max-w-md mx-auto">
            {errorMessage || "We couldn't find a portfolio matching this handle or identifier."}
          </p>
        </div>
        <div className="pt-2">
          <Link
            to="/projects"
            className="inline-flex items-center gap-2 rounded-lg bg-bg-surface border border-border-subtle px-4 py-2 text-xs font-semibold text-text-primary hover:bg-bg-elevated transition-colors"
          >
            <ArrowLeft className="h-4 w-4" aria-hidden="true" />
            <span>Browse Capstone Projects</span>
          </Link>
        </div>
      </main>
    )
  }

  return (
    <main className="min-h-screen bg-bg-base py-8 sm:py-12 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto">
      <PublicPortfolioShowcase portfolio={portfolio} />
    </main>
  )
}
