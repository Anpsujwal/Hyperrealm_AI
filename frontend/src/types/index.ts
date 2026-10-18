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

export interface CitationItem {
  document_id?: string
  title: string
  scope?: 'personal' | 'official' | 'project' | 'historical' | string
  passage?: string
  guideline_version?: string | null
  page_or_section?: string | null
  source_type?: string
  version?: string
  section?: string
}

export interface ProposedActionItem {
  action_type: string
  title: string
  description?: string
  requires_approval: boolean
  payload: Record<string, any>
}

export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  agentId?: AgentId
  attachments?: Attachment[]
  isStreaming?: boolean
  citations?: CitationItem[]
  proposedActions?: ProposedActionItem[]
  delegatedAgents?: string[]
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
  organiser_name?: string
  attendee_ids: string[]
  attendee_names?: Record<string, string>
  project_id?: string | null
  scheduled_at: string
  duration_minutes: number
  location?: string
  agenda?: string[]
  notes?: string
  status?: 'pending' | 'confirmed' | 'rescheduled' | 'rejected' | 'cancelled' | string
  attendee_status?: Record<string, string>
  rejection_reason?: string | null
  proposed_time?: string | null
  rescheduled_by?: string | null
  reschedule_history?: Array<{
    from: string
    to: string
    reason: string
    by_id?: string
    by_name?: string
    at: string
  }>
}

export interface MeetingConflict {
  meeting_id: string
  title: string
  scheduled_at: string
  duration_minutes: number
  conflicting_user_ids: string[]
  conflicting_user_names: string[]
}

export interface CalendarAvailabilityResult {
  available: boolean
  conflicts: MeetingConflict[]
  suggested_slots: string[]
  message: string
}

export interface MeetingRsvpResponse {
  success: boolean
  action: 'accept' | 'reject'
  meeting: MeetingItem
  message: string
  auto_rescheduled: boolean
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
  description?: string
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

export interface DiffLine {
  type: 'added' | 'removed' | 'unchanged'
  text: string
  old_line_no?: number | null
  new_line_no?: number | null
}

export interface SideBySideLine {
  old_line_no?: number | null
  old_text?: string | null
  old_type?: 'removed' | 'unchanged' | 'empty' | null
  new_line_no?: number | null
  new_text?: string | null
  new_type?: 'added' | 'unchanged' | 'empty' | null
}

export interface SemanticChangeSummary {
  change_type: 'breaking' | 'enhancement' | 'deprecation' | 'requirement' | string
  category: string
  description: string
}

export interface GuidelineDiffResponse {
  guideline_id: string
  guideline_title: string
  category: string
  base_version: string
  target_version: string
  available_versions: string[]
  impact_badges: string[]
  impacted_roles: string[]
  impacted_departments: string[]
  impacted_projects: string[]
  severity: 'high' | 'medium' | 'low' | string
  semantic_summary: SemanticChangeSummary[]
  stats: {
    additions: number
    deletions: number
    modifications: number
  }
  unified_diff: DiffLine[]
  side_by_side: SideBySideLine[]
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
  is_manager_approved?: boolean
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
  | 'scrum'
  | 'tasks'
  | 'org-chart'
  | 'admin'
  | 'settings'

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
  { id: 'org-chart', label: 'Organization Chart', path: '/app/org-chart', icon: 'Network' },
  { id: 'admin', label: 'Admin Console', path: '/app/admin', icon: 'ShieldCheck', adminOnly: true },
]

export interface ChatOrchestratorResponse {
  response: string
  agent_id: string
  delegated_agents: string[]
  conversation_id: string
  citations: CitationItem[]
  proposed_actions: ProposedActionItem[]
  requires_approval: boolean
  audit_id?: string | null
  execution_status: string
}

export interface BrandComplianceCheck {
  requirement: string
  observed_evidence: string
  result: string
  supporting_source: string
}

export interface BrandComplianceReportItem {
  id: string
  image_url?: string | null
  image_filename?: string
  guideline_id?: string | null
  guideline_version: string
  status: 'compliant' | 'non_compliant' | 'partially_compliant' | 'unable_to_determine' | string
  summary: string
  checks: BrandComplianceCheck[]
  observed_evidence: Record<string, any>
  guideline_reference: string
  severity: string
  recommendations: string[]
  limitations: string[]
  analysis_status: string
  created_at?: string
}

export interface DocumentSummaryItem {
  document_id: string
  title: string
  summary: string
  key_points?: string[]
  visual_elements_detected?: string[]
  suggested_questions?: string[]
  key_takeaways?: string[]
  citations?: CitationItem[]
  highlights?: string[]
}

export interface DocumentQueryItem {
  document_id: string
  query: string
  answer: string
  citations?: CitationItem[]
}

// ─── Onboarding Types ──────────────────────────────────────────────────────────

export interface OnboardingCourseItem {
  resource_id: string
  title: string
  description: string
  category: string
  estimated_minutes: number
  is_mandatory: boolean
  requires_approval: boolean
  approval_status: 'not_required' | 'pending_approval' | 'approved' | 'rejected' | string
  approval_id?: string | null
  sequence_order: number
  status: string
  progress_pct: number
  reason: string
}

export interface OnboardingIntroduction {
  id: string
  person_id: string
  person_name: string
  role: string
  email: string
  avatar_url?: string | null
  relationship: string
  meeting_purpose: string
  status: 'unassigned' | 'scheduled' | 'completed' | string
  meeting_id?: string | null
}

export interface OnboardingFormRequirement {
  id: string
  title: string
  description: string
  category: string
  is_sensitive: boolean
  status: 'pending' | 'submitted' | 'verified' | 'rejected' | string
  due_days: number
  due_date?: string | null
  submitted_at?: string | null
  reviewed_at?: string | null
  prepopulated_fields?: Record<string, any>
  submitted_data?: Record<string, any>
  feedback_notes?: string
}

export interface OnboardingStep {
  id: string
  phase: string
  title: string
  due_days: number
  status: string
  items: string[]
}

export interface OnboardingJourney {
  id: string
  user_id: string
  user_name?: string | null
  role: string
  department: string
  manager_id?: string | null
  manager_name?: string | null
  buddy_id?: string | null
  buddy_name?: string | null
  start_date: string
  completion_pct: number
  learning_completion_pct: number
  forms_completion_pct: number
  intros_completion_pct: number
  status: string
  courses: OnboardingCourseItem[]
  introductions: OnboardingIntroduction[]
  forms: OnboardingFormRequirement[]
  onboarding_steps: OnboardingStep[]
  onboardingSteps: OnboardingStep[]
  blockers: string[]
  next_action: string
  created_at: string
  updated_at: string
}

