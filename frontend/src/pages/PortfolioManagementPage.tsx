import React, { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Briefcase,
  Plus,
  Loader2,
  AlertCircle,
  RefreshCw,
  FolderGit2,
  Settings,
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import type { PortfolioDetail, PortfolioItem } from '../types/portfolio'
import { portfolioApi } from '../services/portfolioApi'
import { PortfolioProfileEditor } from '../features/portfolio/PortfolioProfileEditor'
import { PortfolioShareCard } from '../features/portfolio/PortfolioShareCard'
import { PortfolioItemCard } from '../features/portfolio/PortfolioItemCard'
import { PortfolioItemModal } from '../features/portfolio/PortfolioItemModal'
import { ApiError } from '../services/api'

export const PortfolioManagementPage: React.FC = () => {
  const { user, loading: authLoading } = useAuth()
  const isAuthenticated = Boolean(user)
  const navigate = useNavigate()

  const [portfolio, setPortfolio] = useState<PortfolioDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Modal states
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [itemToEdit, setItemToEdit] = useState<PortfolioItem | null>(null)
  const [activeTab, setActiveTab] = useState<'items' | 'settings'>('items')

  // Action messages
  const [actionError, setActionError] = useState<string | null>(null)
  const [actionSuccess, setActionSuccess] = useState<string | null>(null)

  const fetchPortfolio = useCallback(async () => {
    setLoading(true)
    setError(null)
    setActionError(null)
    try {
      const data = await portfolioApi.getMyPortfolio()
      setPortfolio(data)
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setError(err.message || 'Unable to load portfolio.')
      } else {
        setError('Failed to load portfolio. Please verify your connection.')
      }
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      navigate('/login?redirect=/portfolio')
      return
    }

    if (isAuthenticated) {
      fetchPortfolio()
    }
  }, [authLoading, isAuthenticated, navigate, fetchPortfolio])

  const handleOpenAddModal = () => {
    setItemToEdit(null)
    setIsModalOpen(true)
  }

  const handleOpenEditModal = (item: PortfolioItem) => {
    setItemToEdit(item)
    setIsModalOpen(true)
  }

  const handleDeleteItem = async (itemId: string) => {
    if (!portfolio) return
    const item = portfolio.items.find((i) => i.id === itemId)
    const confirmed = window.confirm(
      `Remove "${item?.title || 'this item'}" from your portfolio?\n\nNote: This will not delete your project submission or deliverable files.`
    )
    if (!confirmed) return

    try {
      setActionError(null)
      await portfolioApi.deletePortfolioItem(itemId)
      setPortfolio({
        ...portfolio,
        items: portfolio.items.filter((i) => i.id !== itemId),
      })
      setActionSuccess('Item removed from portfolio.')
      setTimeout(() => setActionSuccess(null), 3000)
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setActionError(err.message || 'Failed to remove portfolio item.')
      } else {
        setActionError('Failed to remove portfolio item.')
      }
    }
  }

  const handleMoveUp = async (itemId: string) => {
    if (!portfolio || portfolio.items.length <= 1) return
    const idx = portfolio.items.findIndex((i) => i.id === itemId)
    if (idx <= 0) return

    const newItems = [...portfolio.items]
    const temp = newItems[idx - 1]
    newItems[idx - 1] = newItems[idx]
    newItems[idx] = temp

    // Optimistic update
    setPortfolio({ ...portfolio, items: newItems })

    try {
      const itemIds = newItems.map((i) => i.id)
      const updated = await portfolioApi.reorderPortfolioItems(itemIds)
      setPortfolio({ ...portfolio, items: updated })
    } catch (err: unknown) {
      setActionError('Failed to persist new item order.')
      fetchPortfolio()
    }
  }

  const handleMoveDown = async (itemId: string) => {
    if (!portfolio || portfolio.items.length <= 1) return
    const idx = portfolio.items.findIndex((i) => i.id === itemId)
    if (idx < 0 || idx >= portfolio.items.length - 1) return

    const newItems = [...portfolio.items]
    const temp = newItems[idx + 1]
    newItems[idx + 1] = newItems[idx]
    newItems[idx] = temp

    // Optimistic update
    setPortfolio({ ...portfolio, items: newItems })

    try {
      const itemIds = newItems.map((i) => i.id)
      const updated = await portfolioApi.reorderPortfolioItems(itemIds)
      setPortfolio({ ...portfolio, items: updated })
    } catch (err: unknown) {
      setActionError('Failed to persist new item order.')
      fetchPortfolio()
    }
  }

  if (authLoading || loading) {
    return (
      <main className="min-h-screen bg-bg-base py-12 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto flex flex-col items-center justify-center space-y-4">
        <Loader2 className="h-8 w-8 animate-spin text-accent-violet" aria-hidden="true" />
        <p className="text-sm text-text-muted">Loading your showcase portfolio...</p>
      </main>
    )
  }

  if (error || !portfolio) {
    return (
      <main className="min-h-screen bg-bg-base py-12 px-4 sm:px-6 lg:px-8 max-w-3xl mx-auto text-center space-y-5">
        <div className="inline-flex rounded-full bg-state-error/10 p-4 text-state-error">
          <AlertCircle className="h-8 w-8" aria-hidden="true" />
        </div>
        <h1 className="text-xl font-bold text-text-primary">Unable to Load Portfolio</h1>
        <p className="text-sm text-text-secondary max-w-md mx-auto">{error}</p>
        <button
          type="button"
          onClick={fetchPortfolio}
          className="inline-flex items-center gap-2 rounded-lg bg-accent-violet px-4 py-2 text-sm font-semibold text-white hover:bg-accent-violet-hover transition-colors cursor-pointer"
        >
          <RefreshCw className="h-4 w-4" aria-hidden="true" />
          <span>Retry</span>
        </button>
      </main>
    )
  }

  return (
    <main className="min-h-screen bg-bg-base py-8 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border-subtle pb-6">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Briefcase className="h-5 w-5 text-accent-violet" aria-hidden="true" />
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-text-primary">
              Showcase Portfolio
            </h1>
          </div>
          {portfolio.title && (
            <p className="text-xs font-mono text-accent-cyan">
              {portfolio.title}
            </p>
          )}
          <p className="text-sm text-text-secondary">
            Curate your verified capstone projects, custom deliverables, and demonstrated skills for employers.
          </p>
        </div>

        {/* View Switcher Tabs */}
        <div className="flex items-center gap-1 rounded-xl bg-bg-elevated p-1 border border-border-subtle self-start sm:self-auto">
          <button
            type="button"
            onClick={() => setActiveTab('items')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              activeTab === 'items'
                ? 'bg-accent-violet text-white shadow-sm'
                : 'text-text-secondary hover:text-text-primary'
            }`}
          >
            <FolderGit2 className="h-3.5 w-3.5" aria-hidden="true" />
            <span>Showcase Items ({portfolio.items.length})</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('settings')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              activeTab === 'settings'
                ? 'bg-accent-violet text-white shadow-sm'
                : 'text-text-secondary hover:text-text-primary'
            }`}
          >
            <Settings className="h-3.5 w-3.5" aria-hidden="true" />
            <span>Profile & Links</span>
          </button>
        </div>
      </div>

      {/* Share / Exposure Card */}
      <PortfolioShareCard
        visibility={portfolio.visibility}
        customSlug={portfolio.custom_slug}
        userId={portfolio.user_id}
      />

      {/* Action Notifications */}
      {actionSuccess && (
        <div
          role="status"
          className="rounded-lg bg-state-success/10 border border-state-success/20 p-3 text-xs text-state-success"
        >
          {actionSuccess}
        </div>
      )}

      {actionError && (
        <div
          role="alert"
          className="rounded-lg bg-state-error/10 border border-state-error/20 p-3 text-xs text-state-error flex items-start gap-2"
        >
          <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" aria-hidden="true" />
          <span>{actionError}</span>
        </div>
      )}

      {/* Tab: Items curation */}
      {activeTab === 'items' && (
        <section aria-labelledby="curated-items-heading" className="space-y-6">
          <div className="flex items-center justify-between border-b border-border-subtle/70 pb-3">
            <div>
              <h2 id="curated-items-heading" className="text-base font-bold text-text-primary">
                Featured Portfolio Items
              </h2>
              <p className="text-xs text-text-muted mt-0.5">
                Use the reorder arrows to change the order items appear in your public showcase.
              </p>
            </div>

            <button
              type="button"
              onClick={handleOpenAddModal}
              className="inline-flex items-center gap-1.5 rounded-lg bg-accent-violet px-3.5 py-2 text-xs font-semibold text-white hover:bg-accent-violet-hover transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-violet cursor-pointer"
            >
              <Plus className="h-4 w-4" aria-hidden="true" />
              <span>Add Item</span>
            </button>
          </div>

          {portfolio.items.length > 0 ? (
            <div className="grid grid-cols-1 gap-5">
              {portfolio.items.map((item, idx) => (
                <PortfolioItemCard
                  key={item.id}
                  item={item}
                  isOwner={true}
                  isFirst={idx === 0}
                  isLast={idx === portfolio.items.length - 1}
                  onMoveUp={handleMoveUp}
                  onMoveDown={handleMoveDown}
                  onEdit={handleOpenEditModal}
                  onDelete={handleDeleteItem}
                />
              ))}
            </div>
          ) : (
            <div className="rounded-2xl border border-dashed border-border-medium bg-bg-surface/20 p-12 text-center space-y-4">
              <div className="rounded-full bg-accent-violet/10 p-4 text-accent-violet inline-block">
                <FolderGit2 className="h-8 w-8" aria-hidden="true" />
              </div>
              <div className="space-y-1">
                <h3 className="text-base font-bold text-text-primary">Your Showcase is Empty</h3>
                <p className="text-xs text-text-secondary max-w-sm mx-auto">
                  Add completed capstone projects or custom engineering accomplishments to showcase your skills to employers.
                </p>
              </div>
              <button
                type="button"
                onClick={handleOpenAddModal}
                className="inline-flex items-center gap-2 rounded-lg bg-accent-violet px-4 py-2 text-xs font-semibold text-white hover:bg-accent-violet-hover transition-colors cursor-pointer"
              >
                <Plus className="h-4 w-4" aria-hidden="true" />
                <span>Add Your First Item</span>
              </button>
            </div>
          )}
        </section>
      )}

      {/* Tab: Profile and Links Settings */}
      {activeTab === 'settings' && (
        <PortfolioProfileEditor
          portfolio={portfolio}
          onPortfolioChange={(updated) => setPortfolio(updated)}
        />
      )}

      {/* Add / Edit Modal */}
      <PortfolioItemModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        itemToEdit={itemToEdit}
        onItemSaved={fetchPortfolio}
      />
    </main>
  )
}
