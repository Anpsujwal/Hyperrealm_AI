/**
 * HYPERREALM API Client
 * Centralized HTTP client managing JWT tokens, auth headers, and typed endpoints.
 */
import type {
  ApprovalItem,
  AuditItem,
  DocumentItem,
  GuidelineItem,
  LearningItem,
  MeetingItem,
  NotificationItem,
  OrgNode,
  ProjectItem,
  TaskItem,
  User,
  UserSensitive,
} from '@/types'

const TOKEN_KEY = 'hyperrealm_token'
const API_BASE = '/api/v1'

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY)
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken()
  const headers = new Headers(options.headers || {})

  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
  }

  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  const url = path.startsWith('/api') || path.startsWith('/health') ? path : `${API_BASE}${path}`

  const response = await fetch(url, {
    ...options,
    headers,
  })

  if (response.status === 204) {
    return {} as T
  }

  if (response.status === 401) {
    clearToken()
    window.dispatchEvent(new CustomEvent('hyperrealm:unauthorized'))
  }

  let data: any
  try {
    data = await response.json()
  } catch {
    data = null
  }

  if (!response.ok) {
    const detail = data?.detail || data?.message || `Request failed with status ${response.status}`
    const message = typeof detail === 'string' ? detail : JSON.stringify(detail)
    throw new ApiError(message, response.status)
  }

  return data as T
}

// ─── Domain APIs ─────────────────────────────────────────────────────────────

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: User
}

export interface PaginatedResult<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  has_next?: boolean
  total_pages?: number
}

export const authApi = {
  async login(email: string, password: string): Promise<TokenResponse> {
    const res = await request<TokenResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
    setToken(res.access_token)
    return res
  },

  async signup(name: string, email: string, password: string): Promise<TokenResponse> {
    const res = await request<TokenResponse>('/auth/signup', {
      method: 'POST',
      body: JSON.stringify({ name, email, password }),
    })
    setToken(res.access_token)
    return res
  },

  async getMe(): Promise<User> {
    return request<User>('/auth/me')
  },

  async logout(): Promise<void> {
    try {
      await request('/auth/logout', { method: 'POST' })
    } finally {
      clearToken()
    }
  },
}

export const usersApi = {
  async getOrgTree(): Promise<OrgNode[]> {
    return request<OrgNode[]>('/users/org/tree')
  },

  async getDirectory(): Promise<User[]> {
    return request<User[]>('/users/directory')
  },

  async listUsers(page = 1): Promise<PaginatedResult<User>> {
    return request<PaginatedResult<User>>(`/users?page=${page}&page_size=50`)
  },

  async getUser(userId: string): Promise<User> {
    return request<User>(`/users/${userId}`)
  },

  async getSensitiveDetails(userId: string): Promise<UserSensitive> {
    return request<UserSensitive>(`/users/${userId}/sensitive`)
  },

  async getReports(userId: string): Promise<User[]> {
    return request<User[]>(`/users/${userId}/reports`)
  },
}

export const tasksApi = {
  async listTasks(mine = false): Promise<PaginatedResult<TaskItem>> {
    return request<PaginatedResult<TaskItem>>(`/tasks?page=1&page_size=50&mine=${mine}`)
  },

  async createTask(data: {
    title: string
    description?: string
    assignee_id?: string
    priority?: string
    due_date?: string
    tags?: string[]
  }): Promise<TaskItem> {
    return request<TaskItem>('/tasks', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  async updateTaskStatus(taskId: string, status: string): Promise<TaskItem> {
    return request<TaskItem>(`/tasks/${taskId}/status?status=${status}`, {
      method: 'PATCH',
    })
  },

  async listApprovals(mine = false): Promise<PaginatedResult<ApprovalItem>> {
    return request<PaginatedResult<ApprovalItem>>(`/approvals?page=1&page_size=50&mine=${mine}`)
  },

  async resolveApproval(
    approvalId: string,
    status: 'approved' | 'rejected' | 'approve' | 'reject',
    decision_note = ''
  ): Promise<ApprovalItem> {
    const normalized = status === 'approve' ? 'approved' : status === 'reject' ? 'rejected' : status
    return request<ApprovalItem>(`/approvals/${approvalId}/resolve`, {
      method: 'POST',
      body: JSON.stringify({ status: normalized, decision_note }),
    })
  },
}

export const chatApi = {
  async listConversations(): Promise<PaginatedResult<{ id: string; title: string; agent_id: string; created_at: string }>> {
    return request('/conversations?page=1&page_size=50')
  },

  async createConversation(title = 'New conversation', agent_id = 'auto'): Promise<{ id: string; title: string }> {
    return request('/conversations', {
      method: 'POST',
      body: JSON.stringify({ title, agent_id }),
    })
  },

  async listMessages(convId: string): Promise<PaginatedResult<{ id: string; role: string; content: string; agent_id?: string; created_at: string }>> {
    return request(`/conversations/${convId}/messages?page=1&page_size=100`)
  },

  async sendMessage(convId: string, content: string, agent_id = 'auto'): Promise<{ id: string; role: string; content: string }> {
    return request(`/conversations/${convId}/messages`, {
      method: 'POST',
      body: JSON.stringify({ role: 'user', content, agent_id }),
    })
  },
}

export const knowledgeApi = {
  async listDocuments(category?: string): Promise<PaginatedResult<DocumentItem>> {
    const q = category ? `&category=${encodeURIComponent(category)}` : ''
    return request<PaginatedResult<DocumentItem>>(`/documents?page=1&page_size=50${q}`)
  },

  async listGuidelines(category?: string): Promise<PaginatedResult<GuidelineItem>> {
    const q = category ? `&category=${encodeURIComponent(category)}` : ''
    return request<PaginatedResult<GuidelineItem>>(`/guidelines?page=1&page_size=50${q}`)
  },
}

export const meetingsApi = {
  async listMeetings(mine = false): Promise<PaginatedResult<MeetingItem>> {
    return request<PaginatedResult<MeetingItem>>(`/meetings?page=1&page_size=50&mine=${mine}`)
  },

  async createMeeting(data: {
    title: string
    type?: string
    description?: string
    scheduled_at: string
    duration_minutes?: number
    attendee_ids?: string[]
  }): Promise<MeetingItem> {
    return request<MeetingItem>('/meetings', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },
}

export const learningApi = {
  async listResources(): Promise<PaginatedResult<LearningItem>> {
    return request<PaginatedResult<LearningItem>>('/learning/resources?page=1&page_size=50')
  },

  async myProgress(): Promise<any[]> {
    return request<any[]>('/learning/progress/me')
  },

  async getLearningPaths(role?: string): Promise<{
    role: string
    total: number
    mandatory_count: number
    completed_count: number
    in_progress_count: number
    items: LearningItem[]
  }> {
    const q = role ? `?role=${encodeURIComponent(role)}` : ''
    return request(`/learning/paths${q}`)
  },

  async updateProgress(resourceId: string, status: string, progress_pct: number): Promise<any> {
    return request(`/learning/resources/${resourceId}/progress`, {
      method: 'PUT',
      body: JSON.stringify({ status, progress_pct }),
    })
  },
}

export const adminApi = {
  async listAuditLogs(page = 1): Promise<PaginatedResult<AuditItem>> {
    return request<PaginatedResult<AuditItem>>(`/admin/audit?page=${page}&page_size=50`)
  },

  async listIngestionErrors(): Promise<PaginatedResult<AuditItem>> {
    return request<PaginatedResult<AuditItem>>('/admin/ingestion-errors?page=1&page_size=50')
  },

  async listGuidelineChanges(): Promise<PaginatedResult<GuidelineItem>> {
    return request<PaginatedResult<GuidelineItem>>('/admin/guidelines/changes?page=1&page_size=50')
  },

  async updateGuideline(guideId: string, data: Partial<GuidelineItem>): Promise<GuidelineItem> {
    return request<GuidelineItem>(`/admin/guidelines/${guideId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    })
  },

  async updateDocumentMetadata(docId: string, data: Partial<DocumentItem>): Promise<DocumentItem> {
    return request<DocumentItem>(`/admin/documents/${docId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    })
  },

  async assignLearningRequirements(
    resourceId: string,
    data: { required_for_roles?: string[]; due_days?: number; prerequisites?: string[] }
  ): Promise<LearningItem> {
    return request<LearningItem>(`/admin/learning/${resourceId}/requirements`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  },

  async listDepartments(): Promise<PaginatedResult<any>> {
    return request<PaginatedResult<any>>('/admin/departments')
  },

  async listProjects(mine = false): Promise<PaginatedResult<ProjectItem>> {
    return request<PaginatedResult<ProjectItem>>(`/admin/projects?mine=${mine}`)
  },
}

export const notificationsApi = {
  async listNotifications(unreadOnly = false): Promise<NotificationItem[]> {
    return request<NotificationItem[]>(`/notifications?unread_only=${unreadOnly}`)
  },

  async markRead(notificationId: string): Promise<void> {
    return request<void>(`/notifications/${notificationId}/read`, {
      method: 'POST',
    })
  },

  async markAllRead(): Promise<void> {
    return request<void>('/notifications/read-all', {
      method: 'POST',
    })
  },
}

export const healthApi = {
  async check(): Promise<{ status: string; version: string; environment: string }> {
    return request('/health')
  },
}
