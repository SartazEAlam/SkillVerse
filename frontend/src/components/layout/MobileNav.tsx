import React, { useEffect } from 'react'
import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Compass,
  Network,
  X,
  Sparkles,
  BookOpen
} from 'lucide-react'
import { IconButton } from '../ui/IconButton'

export interface MobileNavProps {
  isOpen: boolean
  onClose: () => void
}

export const MobileNav: React.FC<MobileNavProps> = ({ isOpen, onClose }) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose()
      }
    }
    if (isOpen) {
      document.body.style.overflow = 'hidden'
      window.addEventListener('keydown', handleKeyDown)
    }
    return () => {
      document.body.style.overflow = 'unset'
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [isOpen, onClose])

  if (!isOpen) return null

  const navItems = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/explore', label: 'Explore Courses', icon: Compass },
    { to: '/skills', label: 'Skill Map', icon: Network },
    { to: '/profile', label: 'Profile & Settings', icon: BookOpen }
  ]

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Mobile Navigation"
      className="fixed inset-0 z-50 lg:hidden flex"
    >
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/75 backdrop-blur-sm transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer */}
      <div className="relative w-72 max-w-[80vw] bg-bg-elevated border-r border-border-medium h-full flex flex-col z-10 shadow-2xl">
        {/* Header */}
        <div className="h-16 flex items-center justify-between px-5 border-b border-border-subtle bg-bg-surface/50">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-accent-violet to-accent-cyan flex items-center justify-center text-white">
              <Sparkles className="w-4 h-4" />
            </div>
            <span className="font-bold text-base text-text-primary">SkillVerse</span>
          </div>
          <IconButton
            icon={<X className="w-4 h-4" />}
            aria-label="Close navigation"
            size="sm"
            onClick={onClose}
            className="text-text-muted hover:text-text-primary"
          />
        </div>

        {/* Links */}
        <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
          <div className="px-3 mb-2 text-xs font-semibold uppercase tracking-wider text-text-muted">
            Menu
          </div>
          {navItems.map((item) => {
            const Icon = item.icon
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                onClick={onClose}
                className={({ isActive }) =>
                  `flex items-center gap-3.5 px-4 py-3 rounded-xl font-medium text-sm transition-all ${
                    isActive
                      ? 'bg-accent-violet/15 text-accent-violet border border-accent-violet/30'
                      : 'text-text-secondary hover:text-text-primary hover:bg-bg-surface'
                  }`
                }
              >
                <Icon className="w-5 h-5 shrink-0" />
                <span>{item.label}</span>
              </NavLink>
            )
          })}

          <div className="mt-8 p-4 rounded-xl bg-bg-surface/50 border border-border-subtle space-y-2">
            <div className="flex items-center gap-2 text-xs font-semibold text-text-primary">
              <BookOpen className="w-4 h-4 text-accent-cyan" />
              <span>Current Course</span>
            </div>
            <p className="text-xs text-text-muted">Web Development Foundations</p>
            <div className="w-full bg-bg-inset h-1.5 rounded-full overflow-hidden">
              <div className="bg-accent-cyan h-full w-[45%]" />
            </div>
            <div className="flex justify-between text-[11px] text-text-muted font-mono">
              <span>Progress</span>
              <span>45%</span>
            </div>
          </div>
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-border-subtle bg-bg-surface/30">
          <div className="text-xs text-text-muted">
            <p className="font-semibold text-text-primary">Phase 1 Frontend Shell</p>
            <p className="text-[11px] text-text-muted mt-0.5">Sample data demonstration</p>
          </div>
        </div>
      </div>
    </div>
  )
}
