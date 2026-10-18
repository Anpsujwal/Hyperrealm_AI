/**
 * HYPERREALM API Client
 * Centralized HTTP client managing JWT tokens, auth headers, and typed endpoints.
 */
import type {
  ApprovalItem,
  AuditItem,
  BrandComplianceReportItem,
  ChatOrchestratorResponse,
  CalendarAvailabilityResult,
  DocumentItem,
  DocumentQueryItem,
  DocumentSummaryItem,
  GuidelineDiffResponse,
  GuidelineItem,
  LearningItem,
  MeetingItem,
  MeetingRsvpResponse,
  NotificationItem,
  OnboardingFormRequirement,
  OnboardingJourney,
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
  data?: any
  constructor(message: string, status: number, data?: any) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.data = data
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
    const message = typeof detail === 'string' ? detail : (detail?.message || JSON.stringify(detail))
    throw new ApiError(message, response.status, data?.detail || data)
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

  async orchestrate(params: {
    prompt: string
    agent_id?: string
    conversation_id?: string
    document_ids?: string[]
    image_url?: string
    require_approval?: boolean
  }): Promise<ChatOrchestratorResponse> {
    return request<ChatOrchestratorResponse>('/chat', {
      method: 'POST',
      body: JSON.stringify({
        prompt: params.prompt,
        agent_id: params.agent_id || 'auto',
        conversation_id: params.conversation_id,
        document_ids: params.document_ids,
        image_url: params.image_url,
        require_approval: params.require_approval || false,
      }),
    })
  },

  async deleteConversation(convId: string): Promise<void> {
    return request(`/conversations/${convId}`, { method: 'DELETE' })
  },
}

export const knowledgeApi = {
  async listDocuments(category?: string): Promise<PaginatedResult<DocumentItem>> {
    const q = category ? `&category=${encodeURIComponent(category)}` : ''
    return request<PaginatedResult<DocumentItem>>(`/documents?page=1&page_size=50${q}`)
  },

  async listGuidelines(category?: string): Promise<PaginatedResult<GuidelineItem>> {
    const params = new URLSearchParams({ page: '1', page_size: '50' })
    if (category && category !== 'all') params.append('category', category)
    return request<PaginatedResult<GuidelineItem>>(`/knowledge/official/documents?${params.toString()}`)
  },

  async listPersonalDocuments(category?: string, search?: string): Promise<PaginatedResult<DocumentItem>> {
    const params = new URLSearchParams({ page: '1', page_size: '50' })
    if (category && category !== 'all') params.append('category', category)
    if (search) params.append('search', search)
    return request<PaginatedResult<DocumentItem>>(`/knowledge/personal/documents?${params.toString()}`)
  },

  async uploadPersonalDocument(formData: FormData): Promise<DocumentItem> {
    return request<DocumentItem>('/knowledge/personal/documents/upload', {
      method: 'POST',
      body: formData,
    })
  },

  async deletePersonalDocument(documentId: string): Promise<void> {
    return request<void>(`/documents/${documentId}`, {
      method: 'DELETE',
    })
  },

  async listOfficialGuidelines(category?: string, status_filter?: string): Promise<PaginatedResult<GuidelineItem>> {
    const params = new URLSearchParams({ page: '1', page_size: '50' })
    if (category && category !== 'all') params.append('category', category)
    if (status_filter) params.append('status_filter', status_filter)
    return request<PaginatedResult<GuidelineItem>>(`/knowledge/official/documents?${params.toString()}`)
  },

  async createOfficialGuideline(data: {
    title: string
    content: string
    category: string
    version?: string
    tags?: string[]
    status?: string
    description?: string
    affected_teams?: string[]
    affected_projects?: string[]
    changelog?: string
  }): Promise<GuidelineItem> {
    return request<GuidelineItem>('/knowledge/official/documents', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  async updateOfficialGuideline(guidelineId: string, data: {
    title?: string
    content?: string
    category?: string
    version?: string
    tags?: string[]
    status?: string
    description?: string
    affected_teams?: string[]
    affected_projects?: string[]
    changelog?: string
  }): Promise<GuidelineItem> {
    return request<GuidelineItem>(`/knowledge/official/documents/${guidelineId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    })
  },

  async uploadOfficialGuidelineFile(formData: FormData): Promise<GuidelineItem> {
    return request<GuidelineItem>('/knowledge/official/documents/upload', {
      method: 'POST',
      body: formData,
    })
  },

  async listGuidelineVersions(guidelineId: string): Promise<any[]> {
    return request<any[]>(`/guidelines/${guidelineId}/versions`)
  },

  async createGuidelineVersion(guidelineId: string, data: {
    version: string
    title: string
    content: string
    changelog: string
    status?: string
  }): Promise<GuidelineItem> {
    return request<GuidelineItem>(`/guidelines/${guidelineId}/versions`, {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  async archiveGuideline(guidelineId: string): Promise<GuidelineItem> {
    return request<GuidelineItem>(`/guidelines/${guidelineId}/archive`, {
      method: 'PATCH',
    })
  },

  async getGuidelineDiff(
    guidelineId: string,
    baseVersion?: string,
    targetVersion?: string
  ): Promise<GuidelineDiffResponse> {
    const params = new URLSearchParams()
    if (baseVersion) params.append('base_version', baseVersion)
    if (targetVersion) params.append('target_version', targetVersion)
    const qs = params.toString() ? `?${params.toString()}` : ''
    return request<GuidelineDiffResponse>(`/guidelines/${guidelineId}/diff${qs}`)
  },

  async getDocumentSummary(documentId: string): Promise<DocumentSummaryItem> {
    return request<DocumentSummaryItem>(`/knowledge/documents/${documentId}/summary`, {
      method: 'POST',
      body: JSON.stringify({}),
    })
  },

  async queryDocument(documentId: string, query: string): Promise<DocumentQueryItem> {
    return request<DocumentQueryItem>(`/knowledge/documents/${documentId}/query`, {
      method: 'POST',
      body: JSON.stringify({ query }),
    })
  },

  async auditBrandImage(payload: FormData | { image_filename?: string; image_url?: string; image_base64?: string }): Promise<BrandComplianceReportItem> {
    if (payload instanceof FormData) {
      return request<BrandComplianceReportItem>('/knowledge/images/audit', {
        method: 'POST',
        body: payload,
      })
    }
    return request<BrandComplianceReportItem>('/knowledge/images/audit', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
}

export const actionsApi = {
  async listActions(status_filter?: string): Promise<PaginatedResult<any>> {
    const q = status_filter ? `?status_filter=${encodeURIComponent(status_filter)}` : ''
    return request<PaginatedResult<any>>(`/actions${q}`)
  },

  async executeAction(data: {
    action_type: string
    title: string
    description?: string
    payload?: Record<string, any>
    approval_id?: string
  }): Promise<{
    id: string
    action_type: string
    title: string
    status: string
    result: Record<string, any>
    approval_id?: string | null
    created_at: string
  }> {
    return request('/actions/execute', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },
}

export const meetingsApi = {
  async listMeetings(mine = true): Promise<PaginatedResult<MeetingItem>> {
    return request<PaginatedResult<MeetingItem>>(`/meetings?page=1&page_size=50&mine=${mine}`)
  },

  async createMeeting(data: {
    title: string
    type?: string
    description?: string
    scheduled_at: string
    duration_minutes?: number
    attendee_ids?: string[]
    agenda?: string[]
    notes?: string
    force?: boolean
  }): Promise<MeetingItem> {
    return request<MeetingItem>('/meetings', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  async checkAvailability(data: {
    scheduled_at: string
    duration_minutes?: number
    attendee_ids?: string[]
    exclude_meeting_id?: string
  }): Promise<CalendarAvailabilityResult> {
    return request<CalendarAvailabilityResult>('/meetings/check-availability', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  async rsvpMeeting(
    meetingId: string,
    data: {
      action: 'accept' | 'reject'
      rejection_reason?: string
      proposed_time?: string
    }
  ): Promise<MeetingRsvpResponse> {
    return request<MeetingRsvpResponse>(`/meetings/${meetingId}/rsvp`, {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  async updateMeeting(meetingId: string, data: Partial<MeetingItem>): Promise<MeetingItem> {
    return request<MeetingItem>(`/meetings/${meetingId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    })
  },

  async deleteMeeting(meetingId: string): Promise<void> {
    return request<void>(`/meetings/${meetingId}`, {
      method: 'DELETE',
    })
  },

  async getProposal(proposalId: string): Promise<any> {
    return request<any>(`/meetings/proposals/${proposalId}`)
  },

  async confirmProposal(proposalId: string, idempotency_key?: string): Promise<{
    success: boolean
    meeting: MeetingItem
    proposal: any
    message: string
  }> {
    return request(`/meetings/proposals/${proposalId}/confirm`, {
      method: 'POST',
      body: JSON.stringify({ idempotency_key }),
    })
  },

  async updateProposal(
    proposalId: string,
    data: { scheduled_at?: string; duration_minutes?: number; title?: string; description?: string }
  ): Promise<any> {
    return request(`/meetings/proposals/${proposalId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    })
  },

  async cancelProposal(proposalId: string): Promise<any> {
    return request(`/meetings/proposals/${proposalId}/cancel`, {
      method: 'POST',
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

  async getLearningPaths(role?: string, onlyRoleAndMandatory = true): Promise<{
    role: string
    total: number
    mandatory_count: number
    completed_count: number
    in_progress_count: number
    items: LearningItem[]
  }> {
    const params = new URLSearchParams()
    if (role) params.append('role', role)
    if (onlyRoleAndMandatory) params.append('only_role_and_mandatory', 'true')
    const q = params.toString() ? `?${params.toString()}` : ''
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

export const onboardingApi = {
  async getJourney(): Promise<OnboardingJourney> {
    return request<OnboardingJourney>('/onboarding/journey')
  },

  async regeneratePlan(): Promise<OnboardingJourney> {
    return request<OnboardingJourney>('/onboarding/plan/generate', {
      method: 'POST',
    })
  },

  async getUserJourney(userId: string): Promise<OnboardingJourney> {
    return request<OnboardingJourney>(`/onboarding/user/${userId}`)
  },

  async requestApproval(courseIds: string[], justification: string): Promise<{
    approval: ApprovalItem
    journey: OnboardingJourney
    message: string
  }> {
    return request('/onboarding/request-approval', {
      method: 'POST',
      body: JSON.stringify({ course_ids: courseIds, justification }),
    })
  },

  async listManagerRequests(): Promise<any[]> {
    return request<any[]>('/onboarding/manager/requests')
  },

  async resolveApproval(
    approvalId: string,
    status: 'approved' | 'rejected',
    decisionNote = '',
    approvedCourseIds?: string[]
  ): Promise<{ approval: ApprovalItem; journey?: OnboardingJourney; status: string; message: string }> {
    return request(`/onboarding/approvals/${approvalId}/resolve`, {
      method: 'POST',
      body: JSON.stringify({
        status,
        decision_note: decisionNote,
        approved_course_ids: approvedCourseIds,
      }),
    })
  },

  async scheduleIntro(
    introId: string,
    scheduledAt?: string,
    durationMinutes = 30,
    notes = ''
  ): Promise<{ meeting_id: string; title: string; scheduled_at: string; journey: OnboardingJourney; message: string }> {
    return request('/onboarding/schedule-intro', {
      method: 'POST',
      body: JSON.stringify({
        intro_id: introId,
        scheduled_at: scheduledAt,
        duration_minutes: durationMinutes,
        notes,
      }),
    })
  },

  async listForms(): Promise<OnboardingFormRequirement[]> {
    return request<OnboardingFormRequirement[]>('/onboarding/forms')
  },

  async submitForm(
    formId: string,
    formData: Record<string, any>,
    signatureConfirmation = true
  ): Promise<{ form_id: string; status: string; journey: OnboardingJourney; message: string }> {
    return request(`/onboarding/forms/${formId}/submit`, {
      method: 'POST',
      body: JSON.stringify({
        form_data: formData,
        signature_confirmation: signatureConfirmation,
      }),
    })
  },
}

