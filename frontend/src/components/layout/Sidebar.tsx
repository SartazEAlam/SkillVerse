import React from 'react'
import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Compass,
  Network,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  BookOpen
} from 'lucide-react'

export interface SidebarProps {
  isCollapsed: boolean
  onToggleCollapse: () => void
}

export const Sidebar: React.FC<SidebarProps> = ({ isCollapsed, onToggleCollapse }) => {
  const navItems = [
    {
      to: '/',
      label: 'Dashboard',
      icon: LayoutDashboard,
      badge: undefined
    },
    {
      to: '/explore',
      label: 'Explore Courses',
      icon: Compass,
      badge: '5'
    },
    {
      to: '/skills',
      label: 'Skill Map',
      icon: Network,
      badge: 'Interactive'
    },
    {
      to: '/profile',
      label: 'Profile & Settings',
      icon: BookOpen,
      badge: undefined
    }
  ]

  return (
    <aside
      aria-label="Sidebar Navigation"
      className={`hidden lg:flex flex-col border-r border-border-subtle bg-bg-elevated/70 backdrop-blur-md transition-all duration-300 z-30 select-none ${
        isCollapsed ? 'w-20' : 'w-64'
      }`}
    >
      {/* Brand Header */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-border-subtle">
        <NavLink
          to="/"
          className="flex items-center gap-3 group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-violet rounded-lg p-1"
        >
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-accent-violet to-accent-cyan flex items-center justify-center text-white font-bold shadow-md shadow-accent-violet/20 group-hover:shadow-accent-violet/40 transition-all">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          {!isCollapsed && (
            <div className="flex flex-col">
              <span className="font-bold text-base tracking-tight text-text-primary flex items-center gap-1.5">
                SkillVerse
              </span>
              <span className="text-[10px] uppercase font-mono tracking-wider text-text-muted">
                Interactive Learning
              </span>
            </div>
          )}
        </NavLink>
      </div>

      {/* Main Nav */}
      <div className="flex-1 py-6 px-3 space-y-1.5 overflow-y-auto">
        <div className="mb-3 px-3">
          {!isCollapsed ? (
            <span className="text-[11px] font-semibold uppercase tracking-wider text-text-muted">
              Navigation
            </span>
          ) : (
            <div className="h-2 w-4 mx-auto bg-border-medium rounded-full" />
          )}
        </div>

        {navItems.map((item) => {
          const Icon = item.icon
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3.5 py-2.5 rounded-xl font-medium text-sm transition-all duration-150 relative group ${
                  isActive
                    ? 'bg-accent-violet/15 text-accent-violet shadow-[inset_0_0_0_1px_rgba(139,92,246,0.3)]'
                    : 'text-text-secondary hover:text-text-primary hover:bg-bg-surface/70'
                } ${isCollapsed ? 'justify-center px-0' : ''}`
              }
              title={isCollapsed ? item.label : undefined}
            >
              <Icon className="w-5 h-5 shrink-0 transition-transform group-hover:scale-105" />
              {!isCollapsed && (
                <>
                  <span className="flex-1 truncate">{item.label}</span>
                  {item.badge && (
                    <span className="text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded-md bg-bg-surface text-text-muted border border-border-subtle group-hover:border-border-medium">
                      {item.badge}
                    </span>
                  )}
                </>
              )}
            </NavLink>
          )
        })}

        <div className="pt-6 mb-3 px-3">
          {!isCollapsed ? (
            <span className="text-[11px] font-semibold uppercase tracking-wider text-text-muted">
              Learning Focus
            </span>
          ) : (
            <div className="h-2 w-4 mx-auto bg-border-medium rounded-full" />
          )}
        </div>

        {!isCollapsed && (
          <div className="p-3 mx-1 rounded-xl bg-bg-surface/50 border border-border-subtle space-y-2">
            <div className="flex items-center gap-2 text-xs font-semibold text-text-primary">
              <BookOpen className="w-3.5 h-3.5 text-accent-cyan" />
              <span>Current Path</span>
            </div>
            <p className="text-[11px] text-text-muted line-clamp-2">
              Web Development Foundations • Module 1
            </p>
            <div className="w-full bg-bg-inset h-1.5 rounded-full overflow-hidden">
              <div className="bg-accent-cyan h-full w-[45%]" />
            </div>
            <div className="flex justify-between text-[10px] text-text-muted font-mono">
              <span>Progress</span>
              <span>45%</span>
            </div>
          </div>
        )}
      </div>

      {/* Collapse Toggle & Footer */}
      <div className="p-3 border-t border-border-subtle flex flex-col gap-2">
        <button
          type="button"
          onClick={onToggleCollapse}
          aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          className="flex items-center justify-center gap-2 w-full py-2 px-3 rounded-lg text-text-muted hover:text-text-primary hover:bg-bg-surface text-xs font-medium transition-colors cursor-pointer"
        >
          {isCollapsed ? (
            <ChevronRight className="w-4 h-4" />
          ) : (
            <>
              <ChevronLeft className="w-4 h-4" />
              <span>Collapse Sidebar</span>
            </>
          )}
        </button>

        {!isCollapsed && (
          <div className="px-2 pt-1 flex items-center justify-between text-[11px] text-text-muted font-mono">
            <span>SkillVerse</span>
            <span className="text-accent-violet">v1.0</span>
          </div>
        )}
      </div>
    </aside>
  )
}
