// Shared types for HYPERREALM frontend

export type AgentId = 'knowledge' | 'insights' | 'collaborate' | 'onboard' | 'auto'

export interface Agent {
  id: AgentId
  name: string
  description: string
  color: string
  icon: string
}

export const AGENTS: Agent[] = [
  {
    id: 'auto',
    name: 'Auto Select',
    description: 'HYPERREALM automatically routes to the best agent',
    color: '#6366f1',
    icon: 'Sparkles',
  },
  {
    id: 'knowledge',
    name: 'Knowledge Agent',
    description: 'Retrieves and synthesises internal knowledge and documentation',
    color: '#6366f1',
    icon: 'BookOpen',
  },
  {
    id: 'insights',
    name: 'Insights Agent',
    description: 'Analyzes data, trends, and operational metrics',
    color: '#8b5cf6',
    icon: 'BarChart2',
  },
  {
    id: 'collaborate',
    name: 'Collaborate Agent',
    description: 'Manages tasks, meetings, and team coordination',
    color: '#22d3ee',
    icon: 'Users',
  },
  {
    id: 'onboard',
    name: 'Onboard Agent',
    description: 'Guides onboarding, learning paths, and role-based training',
    color: '#10b981',
    icon: 'GraduationCap',
  },
]

export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  agentId?: AgentId
  attachments?: Attachment[]
  isStreaming?: boolean
}

export interface Attachment {
  id: string
  name: string
  type: string
  size: number
  url?: string
}

export interface Conversation {
  id: string
  title: string
  messages: Message[]
  agentId: AgentId
  createdAt: Date
  updatedAt: Date
}

export type UserRole =
  | 'admin'
  | 'technical_lead'
  | 'project_manager'
  | 'software_developer'
  | 'devops_engineer'
  | 'qa_engineer'
  | 'employee'
  | (string & {})

export interface User {
  id: string
  name: string
  email: string
  role: UserRole
  department?: string
  department_name?: string
  department_id?: string
  job_title?: string
  manager_id?: string | null
  avatarUrl?: string
  avatar_url?: string
  status?: string
  skills?: string[]
  project_ids?: string[]
  created_at?: string
  last_login_at?: string | null
}

export interface UserSensitive extends User {
  employee_code: string
  clearance_level: string
  performance_rating: string
  onboarding_status: string
  contract_type: string
  emergency_contact: string
  salary_band: string
}

export interface TaskItem {
  id: string
  title: string
  description?: string
  status: 'todo' | 'in_progress' | 'in_review' | 'done' | 'blocked' | string
  priority: 'low' | 'medium' | 'high' | 'urgent' | 'critical' | string
  assignee_id?: string | null
  reporter_id: string
  project_id?: string | null
  due_date?: string | null
  tags?: string[]
  created_at: string
}

export interface ApprovalItem {
  id: string
  title: string
  description?: string
  requester_id: string
  approver_id: string
  status: 'pending' | 'approved' | 'rejected' | string
  related_task_id?: string | null
  decision_note?: string
  requested_at: string
  resolved_at?: string | null
}

export interface MeetingItem {
  id: string
  title: string
  type: string
  description?: string
  organiser_id: string
  attendee_ids: string[]
  project_id?: string | null
  scheduled_at: string
  duration_minutes: number
  location?: string
  agenda?: string[]
  notes?: string
}

export interface DocumentItem {
  id: string
  title: string
  content: string
  category: string
  author_id: string
  department_id?: string | null
  is_public?: boolean
  version?: number
  tags?: string[]
  created_at: string
  updated_at?: string
}

export interface GuidelineItem {
  id: string
  title: string
  content: string
  category: string
  owner_id: string
  version?: string
  status?: 'published' | 'draft' | 'review' | 'archived' | string
  effective_date?: string | null
  review_date?: string | null
  tags?: string[]
  affected_teams?: string[]
  affected_projects?: string[]
  changelog?: string
  created_at: string
  updated_at?: string
}

export interface LearningItem {
  id: string
  title: string
  description: string
  category: string
  url?: string
  estimated_minutes: number
  required_for_roles?: string[]
  tags?: string[]
  prerequisites?: string[]
  prerequisites_met?: boolean
  due_days?: number
  due_date?: string | null
  is_mandatory?: boolean
  progress_pct?: number
  status?: 'not_started' | 'in_progress' | 'completed' | string
  started_at?: string | null
  completed_at?: string | null
}

export interface OrgNode {
  user: User
  reports: OrgNode[]
  // Flat compatibility properties if accessed directly
  id?: string
  name?: string
  email?: string
  role?: string
  job_title?: string
  department_name?: string
  direct_reports?: OrgNode[]
}

export interface AuditItem {
  id: string
  actor_id?: string | null
  actor_email?: string | null
  action: string
  resource_type: string
  resource_id?: string | null
  description: string
  ip_address?: string | null
  metadata?: Record<string, any>
  created_at: string
}

export interface NotificationItem {
  id: string
  user_id: string
  type: string
  title: string
  body: string
  is_read: boolean
  link?: string | null
  created_at: string
}

export interface ProjectItem {
  id: string
  name: string
  description: string
  status: string
  owner_id: string
  member_ids: string[]
  department_id?: string | null
  tags: string[]
  start_date?: string | null
  end_date?: string | null
}

export type NavItemId =
  | 'chat'
  | 'dashboard'
  | 'knowledge'
  | 'learning'
  | 'meetings'
  | 'tasks'
  | 'org-chart'
  | 'admin'

export interface NavItem {
  id: NavItemId
  label: string
  path: string
  icon: string
  badge?: number
  adminOnly?: boolean
}

export const NAV_ITEMS: NavItem[] = [
  { id: 'chat', label: 'Chat', path: '/app/chat', icon: 'MessageSquare' },
  { id: 'dashboard', label: 'Dashboard', path: '/app/dashboard', icon: 'LayoutDashboard' },
  { id: 'knowledge', label: 'Knowledge Hub', path: '/app/knowledge', icon: 'BookOpen' },
  { id: 'learning', label: 'My Learning', path: '/app/learning', icon: 'GraduationCap' },
  { id: 'meetings', label: 'Meetings & Scrum', path: '/app/meetings', icon: 'CalendarDays' },
  { id: 'tasks', label: 'Tasks & Approvals', path: '/app/tasks', icon: 'CheckSquare', badge: 3 },
  { id: 'org-chart', label: 'Organization Chart', path: '/app/org-chart', icon: 'Network' },
  { id: 'admin', label: 'Admin Console', path: '/app/admin', icon: 'ShieldCheck', adminOnly: true },
]
