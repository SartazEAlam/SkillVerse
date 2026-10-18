import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Menu, Sparkles, User, Moon } from 'lucide-react'
import { Badge } from '../ui/Badge'

export interface HeaderProps {
  onOpenMobileMenu: () => void
}

export const Header: React.FC<HeaderProps> = ({ onOpenMobileMenu }) => {
  const location = useLocation()

  // Compute current section title from path
  const getPageInfo = () => {
    if (location.pathname === '/') return { title: 'Learner Dashboard', crumb: 'Home' }
    if (location.pathname === '/explore') return { title: 'Explore Skills & Courses', crumb: 'Catalog' }
    if (location.pathname === '/skills') return { title: 'Interactive Skill Map', crumb: 'Taxonomy' }
    if (location.pathname.startsWith('/courses/')) return { title: 'Course Overview', crumb: 'Course' }
    return { title: 'Page Not Found', crumb: '404' }
  }

  const { title, crumb } = getPageInfo()

  return (
    <header className="h-16 border-b border-border-subtle bg-bg-base/80 backdrop-blur-md px-4 sm:px-6 flex items-center justify-between sticky top-0 z-20">
      {/* Left: Mobile hamburger + breadcrumb title */}
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onOpenMobileMenu}
          aria-label="Open mobile navigation menu"
          className="lg:hidden p-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-bg-surface transition-colors cursor-pointer"
        >
          <Menu className="w-5 h-5" />
        </button>

        {/* Brand on mobile */}
        <Link to="/" className="lg:hidden flex items-center gap-2 mr-2">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-accent-violet to-accent-cyan flex items-center justify-center text-white">
            <Sparkles className="w-4 h-4" />
          </div>
        </Link>

        {/* Page Context Breadcrumb */}
        <div className="flex items-center gap-2">
          <span className="hidden sm:inline-block text-xs font-mono text-text-muted">
            {crumb} /
          </span>
          <h1 className="text-sm sm:text-base font-semibold text-text-primary truncate">
            {title}
          </h1>
        </div>
      </div>

      {/* Right: Quick actions & Demo User Profile */}
      <div className="flex items-center gap-3">
        {/* Dark Theme Indicator */}
        <div
          title="Dark Theme (Active). Light theme support planned in Phase 6 preferences."
          className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-bg-surface border border-border-subtle text-xs text-text-muted font-mono"
        >
          <Moon className="w-3.5 h-3.5 text-accent-violet" />
          <span className="text-[11px]">Dark First</span>
        </div>

        {/* Demo Learner Pill */}
        <div
          className="flex items-center gap-2.5 pl-2 pr-3 py-1 rounded-full bg-bg-surface border border-border-subtle"
          title="Demo Learner Account (Sample data only)"
        >
          <div className="w-6 h-6 rounded-full bg-accent-violet/20 border border-accent-violet/40 flex items-center justify-center text-accent-violet text-xs font-bold">
            <User className="w-3.5 h-3.5" />
          </div>
          <div className="flex flex-col text-left">
            <span className="text-xs font-medium text-text-primary leading-tight">
              Alex Morgan
            </span>
          </div>
          <Badge variant="cyan" size="sm" className="hidden md:inline-flex text-[9px] py-0 px-1.5">
            Demo
          </Badge>
        </div>
      </div>
    </header>
  )
}
