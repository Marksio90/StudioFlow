import { AnalyticsSnapshot, CreateProjectInput, ProjectStatus, VideoProject } from './types';
import type { components, operations } from '../../../packages/shared/src/backend-api';

const DEFAULT_TIMEOUT_MS = 10000;
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, '') ?? 'http://localhost:8000';
const DEFAULT_ORGANIZATION_ID = process.env.NEXT_PUBLIC_ORGANIZATION_ID ?? '00000000-0000-0000-0000-000000000001';
const DEFAULT_WORKSPACE_ID = process.env.NEXT_PUBLIC_WORKSPACE_ID ?? '00000000-0000-0000-0000-000000000001';
const DEFAULT_CHANNEL_ID = process.env.NEXT_PUBLIC_CHANNEL_ID ?? '00000000-0000-0000-0000-000000000001';

type ApiRequestOptions = {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  query?: Record<string, string | number | boolean | null | undefined>;
  body?: unknown;
  timeoutMs?: number;
  onLoadingChange?: (isLoading: boolean) => void;
};

type BackendComplianceReport = components['schemas']['ComplianceReportOut'];
type BackendWorkflowEvent = components['schemas']['WorkflowEventOut'];
type BackendAnalyticsSnapshot = components['schemas']['AnalyticsSnapshotOut'];
type BackendVideoProject = components['schemas']['VideoProjectOut'] & {
  ai_cost_usd?: number;
  youtube_quota_used?: number;
  overview?: string;
  research?: string;
  script?: string;
  seo?: string;
  approval_note?: string;
  compliance?: BackendComplianceReport;
  workflow_events?: BackendWorkflowEvent[];
  analytics?: { estimated_ctr: number; projected_views: number };
};

type ListProjectsQuery = operations['list_video_projects_api_v1_video_projects_get']['parameters']['query'];
type CreateProjectBody = operations['create_video_project_api_v1_video_projects_post']['requestBody']['content']['application/json'];
type ApproveProjectBody = operations['approve_api_v1_video_projects__project_id__approve_post']['requestBody']['content']['application/json'];
type RejectProjectBody = operations['reject_api_v1_video_projects__project_id__reject_post']['requestBody']['content']['application/json'];
type ProjectsCollectionResponse = operations['list_video_projects_api_v1_video_projects_get']['responses'][200]['content']['application/json'];

type ApiAdapter = {
  paths: {
    projects: '/api/v1/video-projects';
    projectById: (id: string) => `/api/v1/video-projects/${string}`;
    projectAnalytics: (id: string) => `/api/v1/video-projects/${string}/analytics`;
    projectApprove: (id: string) => `/api/v1/video-projects/${string}/approve`;
    projectReject: (id: string) => `/api/v1/video-projects/${string}/reject`;
  };
  toListProjectsQuery: (filters?: { status?: ProjectStatus; channel?: string }) => ListProjectsQuery;
  toCreateProjectBody: (input: CreateProjectInput) => CreateProjectBody;
  toApprovalBody: (approve: boolean, note?: string) => ApproveProjectBody | RejectProjectBody;
};

export const backendApiAdapter: ApiAdapter = {
  paths: {
    projects: '/api/v1/video-projects',
    projectById: (id) => `/api/v1/video-projects/${id}`,
    projectAnalytics: (id) => `/api/v1/video-projects/${id}/analytics`,
    projectApprove: (id) => `/api/v1/video-projects/${id}/approve`,
    projectReject: (id) => `/api/v1/video-projects/${id}/reject`
  },
  toListProjectsQuery: (filters) => ({
    status: filters?.status,
    channel_id: filters?.channel
  }),
  toCreateProjectBody: (input) => ({
    title: input.title,
    organization_id: DEFAULT_ORGANIZATION_ID,
    workspace_id: DEFAULT_WORKSPACE_ID,
    channel_id: DEFAULT_CHANNEL_ID
  }),
  toApprovalBody: (_approve, note) => ({
    decided_by_user_id: DEFAULT_WORKSPACE_ID,
    comment: note ?? null
  })
};

const buildApiUrl = (path: string, query?: ApiRequestOptions['query']) => {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  const url = new URL(`${API_BASE_URL}${normalizedPath}`);

  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined) url.searchParams.set(key, String(value));
    }
  }

  return url.toString();
};

const mapProjectDto = (dto: BackendVideoProject): VideoProject => ({
  id: dto.id,
  title: dto.title,
  topic: '',
  description: '',
  channel: dto.channel_id,
  language: '',
  targetAudience: '',
  status: dto.status,
  aiCostUsd: dto.ai_cost_usd ?? 0,
  youtubeQuotaUsed: dto.youtube_quota_used ?? 0,
  createdAt: dto.created_at,
  updatedAt: dto.updated_at,
  overview: dto.overview ?? '',
  research: dto.research ?? '',
  script: dto.script ?? '',
  seo: dto.seo ?? '',
  approvalNote: dto.approval_note,
  compliance: {
    score: dto.compliance?.score ?? 0,
    riskLevel: dto.compliance?.risk_level ?? 'low',
    blockingIssues: dto.compliance?.blocking_issues ?? [],
    recommendations: dto.compliance?.recommendations ?? []
  },
  workflowEvents: (dto.workflow_events ?? []).map((event) => ({
    id: event.id,
    timestamp: new Date().toISOString(),
    actor: event.payload?.actor ? String(event.payload.actor) : 'system',
    event: event.event_type
  })),
  analytics: {
    estimatedCtr: dto.analytics?.estimated_ctr ?? 0,
    projectedViews: dto.analytics?.projected_views ?? 0
  }
});

const mapAnalyticsDto = (dto: BackendAnalyticsSnapshot): AnalyticsSnapshot => ({
  id: dto.id,
  videoProjectId: dto.video_project_id,
  channelId: dto.channel_id,
  youtubeVideoId: dto.youtube_video_id,
  views: dto.views,
  watchTimeMinutes: dto.watch_time_minutes,
  averageViewDuration: dto.average_view_duration,
  ctr: dto.ctr,
  likes: dto.likes,
  comments: dto.comments,
  subscribersGained: dto.subscribers_gained,
  estimatedRevenue: dto.estimated_revenue,
  snapshotAt: dto.snapshot_at
});

async function apiRequest<T>(path: string, options: ApiRequestOptions = {}): Promise<T> { /* unchanged */
  const { method = 'GET', query, body, timeoutMs = DEFAULT_TIMEOUT_MS, onLoadingChange } = options;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
  onLoadingChange?.(true);
  try {
    const response = await fetch(buildApiUrl(path, query), { method, headers: { 'Content-Type': 'application/json' }, body: body ? JSON.stringify(body) : undefined, signal: controller.signal });
    if (!response.ok) {
      let details: unknown;
      try { details = await response.json(); } catch { details = await response.text(); }
      throw new Error(`HTTP ${response.status} ${response.statusText}${details ? `: ${JSON.stringify(details)}` : ''}`);
    }
    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') throw new Error(`Request timeout after ${timeoutMs}ms`);
    throw error;
  } finally {
    clearTimeout(timeoutId);
    onLoadingChange?.(false);
  }
}

export const apiClient = {
  buildApiUrl,
  async listProjects(filters?: { status?: ProjectStatus; channel?: string; onLoadingChange?: (isLoading: boolean) => void }) {
    const response = await apiRequest<ProjectsCollectionResponse>(backendApiAdapter.paths.projects, {
      query: backendApiAdapter.toListProjectsQuery(filters),
      onLoadingChange: filters?.onLoadingChange
    });
    return response.items.map(mapProjectDto);
  },
  async getProject(id: string, options?: { onLoadingChange?: (isLoading: boolean) => void }) {
    const project = await apiRequest<BackendVideoProject>(backendApiAdapter.paths.projectById(id), { onLoadingChange: options?.onLoadingChange });
    return mapProjectDto(project);
  },
  async createProject(input: CreateProjectInput, options?: { onLoadingChange?: (isLoading: boolean) => void }) {
    const project = await apiRequest<BackendVideoProject>(backendApiAdapter.paths.projects, {
      method: 'POST',
      body: backendApiAdapter.toCreateProjectBody(input),
      onLoadingChange: options?.onLoadingChange
    });
    return mapProjectDto(project);
  },
  async listAnalytics(id: string, options?: { onLoadingChange?: (isLoading: boolean) => void }): Promise<AnalyticsSnapshot[]> {
    const rows = await apiRequest<BackendAnalyticsSnapshot[]>(backendApiAdapter.paths.projectAnalytics(id), {
      onLoadingChange: options?.onLoadingChange
    });
    return rows.map(mapAnalyticsDto);
  },
  async setApproval(id: string, approve: boolean, note?: string, options?: { onLoadingChange?: (isLoading: boolean) => void }) {
    const path = approve ? backendApiAdapter.paths.projectApprove(id) : backendApiAdapter.paths.projectReject(id);
    const project = await apiRequest<BackendVideoProject>(path, {
      method: 'POST',
      body: backendApiAdapter.toApprovalBody(approve, note),
      onLoadingChange: options?.onLoadingChange
    });
    return mapProjectDto(project);
  }
};
