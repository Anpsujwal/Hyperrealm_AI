import { createContext, useContext, useState, type ReactNode } from 'react'

interface SidebarContextValue {
  isCollapsed: boolean
  toggle: () => void
  collapse: () => void
  expand: () => void
}

const SidebarContext = createContext<SidebarContextValue | null>(null)

export function SidebarProvider({ children }: { children: ReactNode }) {
  const [isCollapsed, setIsCollapsed] = useState(false)

  return (
    <SidebarContext.Provider
      value={{
        isCollapsed,
        toggle: () => setIsCollapsed((v) => !v),
        collapse: () => setIsCollapsed(true),
        expand: () => setIsCollapsed(false),
      }}
    >
      {children}
    </SidebarContext.Provider>
  )
}

export function useSidebar(): SidebarContextValue {
  const ctx = useContext(SidebarContext)
  if (!ctx) throw new Error('useSidebar must be used within <SidebarProvider>')
  return ctx
}
