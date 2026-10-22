import React, { useState } from 'react'
import { Outlet, Link } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { Header } from './Header'
import { MobileNav } from './MobileNav'
import { SkipLink } from '../ui/SkipLink'
import { Sparkles } from 'lucide-react'

import { AuthProvider } from '../../context/AuthContext'

export const Shell: React.FC = () => {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false)
  const [isMobileNavOpen, setIsMobileNavOpen] = useState(false)

  return (
    <AuthProvider>
      <div className="min-h-screen bg-bg-base text-text-primary flex flex-col font-sans selection:bg-accent-violet/30 selection:text-text-primary">
      <SkipLink />

      <div className="flex-1 flex w-full">
        {/* Desktop Sidebar */}
        <Sidebar
          isCollapsed={isSidebarCollapsed}
          onToggleCollapse={() => setIsSidebarCollapsed((prev) => !prev)}
        />

        {/* Mobile Navigation Drawer */}
        <MobileNav
          isOpen={isMobileNavOpen}
          onClose={() => setIsMobileNavOpen(false)}
        />

        {/* Content Wrapper */}
        <div className="flex-1 flex flex-col min-w-0">
          <Header onOpenMobileMenu={() => setIsMobileNavOpen(true)} />

          <main
            id="main-content"
            tabIndex={-1}
            className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8 focus:outline-none"
          >
            <Outlet />
          </main>

          {/* Footer */}
          <footer className="border-t border-border-subtle bg-bg-elevated/40 py-6 px-4 sm:px-6 lg:px-8 text-xs text-text-muted">
            <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="flex items-center gap-2">
                <div className="w-5 h-5 rounded bg-gradient-to-tr from-accent-violet to-accent-cyan flex items-center justify-center text-white">
                  <Sparkles className="w-3 h-3" />
                </div>
                <span className="font-semibold text-text-secondary">SkillVerse Platform</span>
                <span className="text-border-medium">•</span>
                <span>Universal Learning Platform</span>
              </div>

              <div className="flex items-center gap-6">
                <Link to="/explore" className="hover:text-text-primary transition-colors">
                  Course Catalog
                </Link>
                <Link to="/skills" className="hover:text-text-primary transition-colors">
                  Skill Map
                </Link>
                <span className="font-mono text-[11px] text-text-muted">
                  Demo Build v0.1.0
                </span>
              </div>
            </div>
          </footer>
        </div>
      </div>
    </div>
  </AuthProvider>
  )
}
