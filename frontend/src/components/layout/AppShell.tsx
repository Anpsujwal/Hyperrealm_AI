import { Outlet } from 'react-router-dom'
import { AppSidebar } from './AppSidebar'
import { SidebarProvider } from '@/contexts/SidebarContext'

export function AppShell() {
  return (
    <SidebarProvider>
      <div className="flex h-screen overflow-hidden bg-[var(--bg-base)]">
        <AppSidebar />
        <main className="flex-1 overflow-hidden flex flex-col min-w-0">
          <Outlet />
        </main>
      </div>
    </SidebarProvider>
  )
}
