import { Navigate, type RouteObject } from 'react-router-dom'
import { AppShell } from '@/components/layout/AppShell'
import { LandingPage } from '@/pages/LandingPage'
import { LoginPage } from '@/pages/LoginPage'
import { SignupPage } from '@/pages/SignupPage'
import { ChatPage } from '@/pages/ChatPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { KnowledgeHubPage } from '@/pages/KnowledgeHubPage'
import { MyLearningPage } from '@/pages/MyLearningPage'
import { MeetingsPage } from '@/pages/MeetingsPage'
import { TasksPage } from '@/pages/TasksPage'
import { OrgChartPage } from '@/pages/OrgChartPage'
import { AdminConsolePage } from '@/pages/AdminConsolePage'
import { SettingsPage } from '@/pages/SettingsPage'
import { NotFoundPage } from '@/pages/NotFoundPage'

export const routes: RouteObject[] = [
  // Public routes
  { path: '/', element: <LandingPage /> },
  { path: '/login', element: <LoginPage /> },
  { path: '/signup', element: <SignupPage /> },

  // App shell — authenticated layout
  {
    path: '/app',
    element: <AppShell />,
    children: [
      { index: true, element: <Navigate to="/app/chat" replace /> },
      { path: 'chat', element: <ChatPage /> },
      { path: 'dashboard', element: <DashboardPage /> },
      { path: 'knowledge', element: <KnowledgeHubPage /> },
      { path: 'learning', element: <MyLearningPage /> },
      { path: 'meetings', element: <MeetingsPage /> },
      { path: 'tasks', element: <TasksPage /> },
      { path: 'org-chart', element: <OrgChartPage /> },
      { path: 'admin', element: <AdminConsolePage /> },
      { path: 'settings', element: <SettingsPage /> },
      { path: 'notifications', element: <Navigate to="/app/dashboard" replace /> },
    ],
  },

  // Catch-all
  { path: '*', element: <NotFoundPage /> },
]
