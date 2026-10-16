import { NavLink, useNavigate } from 'react-router-dom'
import {
  MessageSquare,
  LayoutDashboard,
  BookOpen,
  GraduationCap,
  CalendarDays,
  CheckSquare,
  Network,
  ShieldCheck,
  Settings,
  LogOut,
  Sparkles,
  Sun,
  Moon,
  PanelLeftClose,
  PanelLeftOpen,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useSidebar } from '@/contexts/SidebarContext'
import { useAuth } from '@/contexts/AuthContext'
import { useTheme } from '@/contexts/ThemeContext'
import { Avatar } from '@/components/ui/Avatar'
import type { NavItem } from '@/types'
import * as TooltipPrimitive from '@radix-ui/react-tooltip'

// Icon map
const ICON_MAP: Record<string, React.ComponentType<{ className?: string }>> = {
  MessageSquare,
  LayoutDashboard,
  BookOpen,
  GraduationCap,
  CalendarDays,
  CheckSquare,
  Network,
  ShieldCheck,
}

interface NavGroup {
  label: string
  items: NavItem[]
}

const NAV_GROUPS: NavGroup[] = [
  {
    label: 'Workspace',
    items: [
      { id: 'dashboard', label: 'Dashboard', path: '/app/dashboard', icon: 'LayoutDashboard' },
      { id: 'chat', label: 'AI Copilot', path: '/app/chat', icon: 'MessageSquare' },
      { id: 'tasks', label: 'Tasks & Approvals', path: '/app/tasks', icon: 'CheckSquare', badge: 3 },
      { id: 'meetings', label: 'Meetings & Scrum', path: '/app/meetings', icon: 'CalendarDays' },
    ],
  },
  {
    label: 'Knowledge & Org',
    items: [
      { id: 'knowledge', label: 'Knowledge Hub', path: '/app/knowledge', icon: 'BookOpen' },
      { id: 'learning', label: 'My Learning', path: '/app/learning', icon: 'GraduationCap' },
      { id: 'org-chart', label: 'Organization Chart', path: '/app/org-chart', icon: 'Network' },
    ],
  },
  {
    label: 'Management',
    items: [
      { id: 'admin', label: 'Admin Console', path: '/app/admin', icon: 'ShieldCheck', adminOnly: true },
    ],
  },
]

function SidebarNavItem({ item, isCollapsed }: { item: NavItem; isCollapsed: boolean }) {
  const Icon = ICON_MAP[item.icon] ?? MessageSquare

  if (isCollapsed) {
    return (
      <TooltipPrimitive.Provider delayDuration={100}>
        <TooltipPrimitive.Root>
          <TooltipPrimitive.Trigger asChild>
            <NavLink
              to={item.path}
              className={({ isActive }) =>
                cn(
                  'relative flex items-center justify-center h-10 w-10 mx-auto rounded-xl text-sm font-medium transition-all duration-200',
                  isActive
                    ? 'bg-gradient-to-tr from-blue-500/15 via-purple-500/15 to-rose-500/10 text-[var(--accent-indigo)] border border-purple-500/30 shadow-sm'
                    : 'text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)]'
                )
              }
            >
              {({ isActive }) => (
                <>
                  <Icon
                    className={cn(
                      'h-4.5 w-4.5 transition-transform duration-150',
                      isActive ? 'text-[var(--accent-indigo)] scale-105' : 'text-[var(--text-muted)]'
                    )}
                  />
                  {item.badge != null && item.badge > 0 && (
                    <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 ring-2 ring-[var(--bg-surface)]" />
                  )}
                </>
              )}
            </NavLink>
          </TooltipPrimitive.Trigger>

          <TooltipPrimitive.Portal>
            <TooltipPrimitive.Content
              side="right"
              sideOffset={10}
              className="z-50 px-3 py-1.5 text-xs font-semibold rounded-xl bg-[var(--bg-overlay)] border border-[var(--border-strong)] text-[var(--text-primary)] shadow-xl backdrop-blur-md"
            >
              {item.label}
              {item.badge != null && item.badge > 0 && (
                <span className="ml-2 px-1.5 py-0.5 rounded-full text-[10px] bg-purple-500/20 text-purple-400 font-bold">
                  {item.badge}
                </span>
              )}
              <TooltipPrimitive.Arrow className="fill-[var(--border-strong)]" />
            </TooltipPrimitive.Content>
          </TooltipPrimitive.Portal>
        </TooltipPrimitive.Root>
      </TooltipPrimitive.Provider>
    )
  }

  return (
    <NavLink
      to={item.path}
      className={({ isActive }) =>
        cn(
          'group relative flex items-center gap-3 w-full px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 select-none',
          isActive
            ? 'bg-gradient-to-r from-blue-500/15 via-purple-500/10 to-transparent text-[var(--accent-indigo)] font-semibold border border-purple-500/20 shadow-sm'
            : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)]'
        )
      }
    >
      {({ isActive }) => (
        <>
          {/* Subtle left active bar */}
          {isActive && (
            <span className="absolute left-0 top-2 bottom-2 w-1 rounded-r-full bg-gradient-to-b from-[#4285f4] via-[#9b72cf] to-[#d96570]" />
          )}

          <Icon
            className={cn(
              'h-4.5 w-4.5 flex-shrink-0 transition-colors',
              isActive ? 'text-[var(--accent-indigo)]' : 'text-[var(--text-muted)] group-hover:text-[var(--text-primary)]'
            )}
          />

          <span className="truncate flex-1 text-left">{item.label}</span>

          {item.badge != null && item.badge > 0 && (
            <span className="ml-auto px-2 py-0.5 text-xs font-semibold rounded-full bg-purple-500/15 text-purple-400 border border-purple-500/20">
              {item.badge}
            </span>
          )}
        </>
      )}
    </NavLink>
  )
}

export function AppSidebar() {
  const { isCollapsed, toggle } = useSidebar()
  const { user, logout } = useAuth()
  const { resolvedTheme, toggleTheme } = useTheme()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  return (
    <aside
      className={cn(
        'relative flex flex-col h-full flex-shrink-0 select-none',
        'bg-[var(--bg-surface)] border-r border-[var(--border-default)]',
        'transition-[width] duration-200 ease-in-out z-20',
        isCollapsed ? 'w-16' : 'w-64'
      )}
      aria-label="Main navigation"
    >
      {/* ─── Header / Brand ──────────────────────────────────────────────── */}
      <div
        className={cn(
          'flex items-center h-16 px-3.5 border-b border-[var(--border-default)] flex-shrink-0',
          isCollapsed ? 'justify-center' : 'justify-between'
        )}
      >
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="relative flex-shrink-0 h-9 w-9 rounded-xl bg-gradient-to-tr from-[#4285f4] via-[#9b72cf] to-[#d96570] flex items-center justify-center shadow-[0_0_20px_rgba(155,114,207,0.35)]">
            <Sparkles className="h-4.5 w-4.5 text-white" />
          </div>
          {!isCollapsed && (
            <div className="flex flex-col min-w-0">
              <div className="flex items-center gap-1.5">
                <span className="font-display text-sm font-bold tracking-tight text-[var(--text-primary)] leading-tight">
                  HYPERREALM
                </span>
                <span className="px-1.5 py-0.5 text-[9px] font-semibold rounded-full bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-rose-500/10 text-purple-600 dark:text-purple-300 border border-purple-500/25 leading-none">
                  AI OS
                </span>
              </div>
              <span className="text-[11px] text-[var(--text-muted)] truncate leading-tight font-medium">
                Enterprise Intelligence
              </span>
            </div>
          )}
        </div>

        {/* Header collapse toggle */}
        {!isCollapsed && (
          <button
            onClick={toggle}
            className="p-1 rounded-md text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] transition-colors cursor-pointer"
            title="Collapse sidebar"
            aria-label="Collapse sidebar"
          >
            <PanelLeftClose className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* ─── Collapsed Expand Button ──────────────────────────────────────── */}
      {isCollapsed && (
        <div className="flex justify-center pt-2 pb-1 flex-shrink-0">
          <button
            onClick={toggle}
            className="p-1.5 rounded-lg text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] transition-colors cursor-pointer"
            title="Expand sidebar"
            aria-label="Expand sidebar"
          >
            <PanelLeftOpen className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* ─── Navigation Groups ───────────────────────────────────────────── */}
      <nav className="flex-1 overflow-y-auto overflow-x-hidden py-3 px-2 space-y-4 scrollbar-hide">
        {NAV_GROUPS.map((group) => {
          const visibleItems = group.items.filter(
            (item) => !item.adminOnly || user?.role === 'admin'
          )
          if (visibleItems.length === 0) return null

          return (
            <div key={group.label} className="space-y-1">
              {!isCollapsed && (
                <div className="px-3 pb-1 text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)]">
                  {group.label}
                </div>
              )}
              {visibleItems.map((item) => (
                <SidebarNavItem key={item.id} item={item} isCollapsed={isCollapsed} />
              ))}
            </div>
          )
        })}
      </nav>

      {/* ─── Footer Section ─────────────────────────────────────────────── */}
      <div className="flex-shrink-0 border-t border-[var(--border-default)] p-2 space-y-1.5 bg-[var(--bg-surface)]">
        {/* Theme switcher */}
        {isCollapsed ? (
          <TooltipPrimitive.Provider delayDuration={100}>
            <TooltipPrimitive.Root>
              <TooltipPrimitive.Trigger asChild>
                <button
                  onClick={toggleTheme}
                  className="flex items-center justify-center h-10 w-10 mx-auto rounded-lg text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] transition-colors cursor-pointer"
                  aria-label="Toggle theme"
                >
                  {resolvedTheme === 'dark' ? (
                    <Sun className="h-4 w-4 text-amber-400" />
                  ) : (
                    <Moon className="h-4 w-4 text-indigo-500" />
                  )}
                </button>
              </TooltipPrimitive.Trigger>
              <TooltipPrimitive.Portal>
                <TooltipPrimitive.Content
                  side="right"
                  sideOffset={10}
                  className="z-50 px-2.5 py-1 text-xs font-medium rounded-lg bg-[var(--bg-overlay)] border border-[var(--border-strong)] text-[var(--text-primary)] shadow-md"
                >
                  Switch to {resolvedTheme === 'dark' ? 'Light' : 'Dark'} mode
                  <TooltipPrimitive.Arrow className="fill-[var(--border-strong)]" />
                </TooltipPrimitive.Content>
              </TooltipPrimitive.Portal>
            </TooltipPrimitive.Root>
          </TooltipPrimitive.Provider>
        ) : (
          <button
            onClick={toggleTheme}
            className="flex items-center justify-between w-full px-3 py-2 rounded-lg text-xs font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] transition-colors cursor-pointer"
          >
            <div className="flex items-center gap-2.5">
              {resolvedTheme === 'dark' ? (
                <Sun className="h-4 w-4 text-amber-400" />
              ) : (
                <Moon className="h-4 w-4 text-indigo-500" />
              )}
              <span>Theme</span>
            </div>
            <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded bg-[var(--bg-elevated)] border border-[var(--border-default)] text-[var(--text-muted)]">
              {resolvedTheme}
            </span>
          </button>
        )}

        {/* Settings link */}
        {isCollapsed ? (
          <TooltipPrimitive.Provider delayDuration={100}>
            <TooltipPrimitive.Root>
              <TooltipPrimitive.Trigger asChild>
                <NavLink
                  to="/app/settings"
                  className={({ isActive }) =>
                    cn(
                      'flex items-center justify-center h-10 w-10 mx-auto rounded-lg transition-colors',
                      isActive
                        ? 'bg-indigo-500/15 text-[var(--accent-indigo)]'
                        : 'text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)]'
                    )
                  }
                >
                  <Settings className="h-4 w-4" />
                </NavLink>
              </TooltipPrimitive.Trigger>
              <TooltipPrimitive.Portal>
                <TooltipPrimitive.Content
                  side="right"
                  sideOffset={10}
                  className="z-50 px-2.5 py-1 text-xs font-medium rounded-lg bg-[var(--bg-overlay)] border border-[var(--border-strong)] text-[var(--text-primary)] shadow-md"
                >
                  Settings
                  <TooltipPrimitive.Arrow className="fill-[var(--border-strong)]" />
                </TooltipPrimitive.Content>
              </TooltipPrimitive.Portal>
            </TooltipPrimitive.Root>
          </TooltipPrimitive.Provider>
        ) : (
          <NavLink
            to="/app/settings"
            className={({ isActive }) =>
              cn(
                'flex items-center gap-2.5 w-full px-3 py-2 rounded-lg text-xs font-medium transition-colors',
                isActive
                  ? 'bg-indigo-500/10 text-[var(--accent-indigo)] font-semibold'
                  : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)]'
              )
            }
          >
            <Settings className="h-4 w-4 text-[var(--text-muted)]" />
            <span>Settings</span>
          </NavLink>
        )}

        {/* User profile card */}
        <div
          className={cn(
            'flex items-center gap-2.5 p-2 rounded-lg border border-[var(--border-default)] bg-[var(--bg-elevated)]',
            isCollapsed && 'justify-center p-1.5'
          )}
        >
          <Avatar name={user?.name ?? 'User'} size="sm" statusDot="online" />
          {!isCollapsed && (
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold text-[var(--text-primary)] truncate leading-tight">
                {user?.name ?? 'User'}
              </p>
              <p className="text-[10px] text-[var(--text-muted)] truncate capitalize leading-tight">
                {user?.role?.replace(/_/g, ' ') ?? 'Member'}
              </p>
            </div>
          )}
          {!isCollapsed && (
            <button
              onClick={handleLogout}
              className="text-[var(--text-muted)] hover:text-[var(--accent-rose)] hover:bg-rose-500/10 transition-colors p-1 rounded cursor-pointer"
              title="Sign out"
              aria-label="Sign out"
            >
              <LogOut className="h-3.5 w-3.5" />
            </button>
          )}
        </div>
      </div>
    </aside>
  )
}
