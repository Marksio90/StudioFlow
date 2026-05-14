import { AnalyticsSnapshot, CreateProjectInput, ProjectStatus, VideoProject } from './types';

const DEFAULT_TIMEOUT_MS = 10000;
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, '') ?? 'http://localhost:8000';

type ApiRequestOptions = {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  query?: Record<string, string | number | boolean | undefined>;
  body?: unknown;
  timeoutMs?: number;
  onLoadingChange?: (isLoading: boolean) => void;
};

interface BackendComplianceReport {
  score: number;
  risk_level: 'low' | 'medium' | 'high';
  blocking_issues: string[];
  recommendations: string[];
}

interface BackendWorkflowEvent {
  id: string;
  timestamp: string;
  actor: string;
  event: string;
}

interface BackendVideoProject {
  id: string;
  title: string;
  topic: string;
  description: string;
  channel: string;
  language: string;
  target_audience: string;
  status: ProjectStatus;
  ai_cost_usd: number;
  youtube_quota_used: number;
  created_at: string;
  updated_at: string;
  overview: string;
  research: string;
  script: string;
  seo: string;
  approval_note?: string;
  compliance: BackendComplianceReport;
  workflow_events: BackendWorkflowEvent[];
  analytics: { estimated_ctr: number; projected_views: number };
}

interface BackendAnalyticsSnapshot {
  id: string;
  video_project_id: string;
  channel_id: string;
  youtube_video_id: string;
  views: number;
  watch_time_minutes: number;
  average_view_duration: number;
  ctr: number;
  likes: number;
  comments: number;
  subscribers_gained: number;
  estimated_revenue: number;
  snapshot_at: string;
}

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
  topic: dto.topic,
  description: dto.description,
  channel: dto.channel,
  language: dto.language,
  targetAudience: dto.target_audience,
  status: dto.status,
  aiCostUsd: dto.ai_cost_usd,
  youtubeQuotaUsed: dto.youtube_quota_used,
  createdAt: dto.created_at,
  updatedAt: dto.updated_at,
  overview: dto.overview,
  research: dto.research,
  script: dto.script,
  seo: dto.seo,
  approvalNote: dto.approval_note,
  compliance: {
    score: dto.compliance.score,
    riskLevel: dto.compliance.risk_level,
    blockingIssues: dto.compliance.blocking_issues,
    recommendations: dto.compliance.recommendations
  },
  workflowEvents: dto.workflow_events,
  analytics: {
    estimatedCtr: dto.analytics.estimated_ctr,
    projectedViews: dto.analytics.projected_views
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

async function apiRequest<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
  const { method = 'GET', query, body, timeoutMs = DEFAULT_TIMEOUT_MS, onLoadingChange } = options;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  onLoadingChange?.(true);

  try {
    const response = await fetch(buildApiUrl(path, query), {
      method,
      headers: {
        'Content-Type': 'application/json'
      },
      body: body ? JSON.stringify(body) : undefined,
      signal: controller.signal
    });

    if (!response.ok) {
      let details: unknown;
      try {
        details = await response.json();
      } catch {
        details = await response.text();
      }
      throw new Error(`HTTP ${response.status} ${response.statusText}${details ? `: ${JSON.stringify(details)}` : ''}`);
    }

    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new Error(`Request timeout after ${timeoutMs}ms`);
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
    onLoadingChange?.(false);
  }
}

export const apiClient = {
  buildApiUrl,
  async listProjects(filters?: { status?: ProjectStatus; channel?: string; onLoadingChange?: (isLoading: boolean) => void }) {
    const rows = await apiRequest<BackendVideoProject[]>('/projects', {
      query: { status: filters?.status, channel: filters?.channel },
      onLoadingChange: filters?.onLoadingChange
    });
    return rows.map(mapProjectDto);
  },
  async getProject(id: string, options?: { onLoadingChange?: (isLoading: boolean) => void }) {
    const project = await apiRequest<BackendVideoProject>(`/projects/${id}`, { onLoadingChange: options?.onLoadingChange });
    return mapProjectDto(project);
  },
  async createProject(input: CreateProjectInput, options?: { onLoadingChange?: (isLoading: boolean) => void }) {
    const project = await apiRequest<BackendVideoProject>('/projects', {
      method: 'POST',
      body: {
        title: input.title,
        topic: input.topic,
        description: input.description,
        channel: input.channel,
        language: input.language,
        target_audience: input.targetAudience
      },
      onLoadingChange: options?.onLoadingChange
    });
    return mapProjectDto(project);
  },
  async listAnalytics(id: string, options?: { onLoadingChange?: (isLoading: boolean) => void }): Promise<AnalyticsSnapshot[]> {
    const rows = await apiRequest<BackendAnalyticsSnapshot[]>(`/projects/${id}/analytics`, {
      onLoadingChange: options?.onLoadingChange
    });
    return rows.map(mapAnalyticsDto);
  },
  async setApproval(id: string, approve: boolean, note?: string, options?: { onLoadingChange?: (isLoading: boolean) => void }) {
    const project = await apiRequest<BackendVideoProject>(`/projects/${id}/approval`, {
      method: 'POST',
      body: { approve, note },
      onLoadingChange: options?.onLoadingChange
    });
    return mapProjectDto(project);
  }
};
