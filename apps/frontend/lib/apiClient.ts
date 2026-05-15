import { AnalyticsSnapshot, Channel, ChannelMemory, ChannelMemoryInput, ContentIdea, ContentIdeaStatus, CreateChannelInput, CreateContentIdeaInput, CreateProjectInput, IdeaResearchRecommendation, IdeaResearchReport, NicheReport, ProjectStatus, UpdateChannelInput, UpdateContentIdeaInput, VideoProject } from './types';
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
type BackendChannel = components['schemas']['ChannelOut'];
type BackendChannelMemoryOut = components['schemas']['ChannelMemoryOut'];
type BackendChannelMemoryPayload = components['schemas']['ChannelMemoryPayload'];
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


type BackendContentIdea = {
  id: string;
  organization_id: string;
  workspace_id: string;
  channel_id: string;
  title: string;
  summary?: string | null;
  content_pillar: string;
  status: ContentIdeaStatus;
  created_at: string;
  updated_at: string;
};

type ListProjectsQuery = operations['list_video_projects_api_v1_video_projects_get']['parameters']['query'];
type CreateProjectBody = operations['create_video_project_api_v1_video_projects_post']['requestBody']['content']['application/json'];
type ApproveProjectBody = operations['approve_api_v1_video_projects__project_id__approve_post']['requestBody']['content']['application/json'];
type RejectProjectBody = operations['reject_api_v1_video_projects__project_id__reject_post']['requestBody']['content']['application/json'];
type ProjectsCollectionResponse = operations['list_video_projects_api_v1_video_projects_get']['responses'][200]['content']['application/json'];
type ChannelsCollectionResponse = operations['list_channels_api_v1_channels_get']['responses'][200]['content']['application/json'];

type ApiAdapter = {
  paths: {
    projects: '/api/v1/video-projects';
    projectById: (id: string) => `/api/v1/video-projects/${string}`;
    projectAnalytics: (id: string) => `/api/v1/video-projects/${string}/analytics`;
    projectApprove: (id: string) => `/api/v1/video-projects/${string}/approve`;
    projectReject: (id: string) => `/api/v1/video-projects/${string}/reject`;
    channels: '/api/v1/channels';
    channelById: (id: string) => `/api/v1/channels/${string}`;
    channelMemory: (id: string) => `/api/v1/channels/${string}/memory`;
    nicheAnalyze: (id: string) => `/api/v1/channels/${string}/niche/analyze`;
    nicheReports: (id: string) => `/api/v1/channels/${string}/niche/reports`;
    nicheReportById: (id: string, reportId: string) => `/api/v1/channels/${string}/niche/reports/${string}`;
    ideas: '/api/v1/content-ideas';
    ideaById: (id: string) => `/api/v1/content-ideas/${string}`;
    ideaStatus: (id: string) => `/api/v1/content-ideas/${string}/status`;
    ideaResearchAnalyze: (id: string) => `/api/v1/content-ideas/${string}/research/analyze`;
    ideaResearchLatest: (id: string) => `/api/v1/content-ideas/${string}/research/latest`;
    ideaResearchReports: (id: string) => `/api/v1/content-ideas/${string}/research/reports`;
  };
  toListProjectsQuery: (filters?: { status?: ProjectStatus; channel?: string }) => ListProjectsQuery;
  toCreateProjectBody: (input: CreateProjectInput) => CreateProjectBody;
  toCreateChannelBody: (input: CreateChannelInput) => { organization_id: string; workspace_id: string; name: string; youtube_channel_id: string };
  toPatchChannelBody: (input: UpdateChannelInput) => { name?: string; youtube_channel_id?: string };
  toChannelMemoryBody: (input: ChannelMemoryInput) => BackendChannelMemoryPayload;
  toApprovalBody: (approve: boolean, note?: string) => ApproveProjectBody | RejectProjectBody;
  toCreateIdeaBody: (input: CreateContentIdeaInput) => { organization_id: string; workspace_id: string; channel_id: string; title: string; summary?: string; content_pillar: string };
  toUpdateIdeaBody: (input: UpdateContentIdeaInput) => { title?: string; summary?: string; content_pillar?: string };
  toListIdeasQuery: (filters?: { status?: ContentIdeaStatus; contentPillar?: string; query?: string }) => Record<string, string | undefined>;

};

export const backendApiAdapter: ApiAdapter = {
  paths: {
    projects: '/api/v1/video-projects', projectById: (id) => `/api/v1/video-projects/${id}`, projectAnalytics: (id) => `/api/v1/video-projects/${id}/analytics`, projectApprove: (id) => `/api/v1/video-projects/${id}/approve`, projectReject: (id) => `/api/v1/video-projects/${id}/reject`,
    channels: '/api/v1/channels', channelById: (id) => `/api/v1/channels/${id}`, channelMemory: (id) => `/api/v1/channels/${id}/memory`, nicheAnalyze: (id) => `/api/v1/channels/${id}/niche/analyze`, nicheReports: (id) => `/api/v1/channels/${id}/niche/reports`, nicheReportById: (id, reportId) => `/api/v1/channels/${id}/niche/reports/${reportId}`,
    ideas: '/api/v1/content-ideas', ideaById: (id) => `/api/v1/content-ideas/${id}`, ideaStatus: (id) => `/api/v1/content-ideas/${id}/status`, ideaResearchAnalyze: (id) => `/api/v1/content-ideas/${id}/research/analyze`, ideaResearchLatest: (id) => `/api/v1/content-ideas/${id}/research/latest`, ideaResearchReports: (id) => `/api/v1/content-ideas/${id}/research/reports`
  },
  toListProjectsQuery: (filters) => ({ status: filters?.status, channel_id: filters?.channel }),
  toCreateProjectBody: (input) => ({ title: input.title, organization_id: DEFAULT_ORGANIZATION_ID, workspace_id: DEFAULT_WORKSPACE_ID, channel_id: DEFAULT_CHANNEL_ID }),
  toCreateChannelBody: (input) => ({ organization_id: DEFAULT_ORGANIZATION_ID, workspace_id: DEFAULT_WORKSPACE_ID, name: input.name, youtube_channel_id: input.youtubeChannelId }),
  toPatchChannelBody: (input) => ({ ...(input.name !== undefined ? { name: input.name } : {}), ...(input.youtubeChannelId !== undefined ? { youtube_channel_id: input.youtubeChannelId } : {}) }),
  toChannelMemoryBody: (input) => ({
    approved_title_patterns: input.approvedTitlePatterns,
    rejected_title_patterns: input.rejectedTitlePatterns,
    thumbnail_rules: input.thumbnailRules,
    banned_phrases: input.bannedPhrases,
    preferred_phrases: input.preferredPhrases,
    compliance_preferences: input.compliancePreferences,
    narrator_style: input.narratorStyle,
    visual_style: input.visualStyle,
    audience_objections: input.audienceObjections,
    best_performing_patterns: input.bestPerformingPatterns,
    worst_performing_patterns: input.worstPerformingPatterns,
    freeform_memory_notes: input.freeformMemoryNotes
  }),
  toApprovalBody: (_approve, note) => ({ decided_by_user_id: DEFAULT_WORKSPACE_ID, comment: note ?? null }),
  toCreateIdeaBody: (input) => ({ organization_id: DEFAULT_ORGANIZATION_ID, workspace_id: DEFAULT_WORKSPACE_ID, channel_id: DEFAULT_CHANNEL_ID, title: input.title, ...(input.summary ? { summary: input.summary } : {}), content_pillar: input.contentPillar }),
  toUpdateIdeaBody: (input) => ({ ...(input.title !== undefined ? { title: input.title } : {}), ...(input.summary !== undefined ? { summary: input.summary } : {}), ...(input.contentPillar !== undefined ? { content_pillar: input.contentPillar } : {}) }),
  toListIdeasQuery: (filters) => ({ status: filters?.status, content_pillar: filters?.contentPillar, q: filters?.query })
};

const buildApiUrl = (path: string, query?: ApiRequestOptions['query']) => {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  const url = new URL(`${API_BASE_URL}${normalizedPath}`);
  if (query) for (const [key, value] of Object.entries(query)) if (value !== undefined) url.searchParams.set(key, String(value));
  return url.toString();
};

const mapChannelDto = (dto: BackendChannel): Channel => ({
  id: dto.id,
  organizationId: dto.organization_id,
  workspaceId: dto.workspace_id,
  name: dto.name,
  youtubeChannelId: dto.youtube_channel_id,
  createdAt: dto.created_at,
  updatedAt: dto.updated_at
});

const mapChannelMemory = (dto: BackendChannelMemoryOut): ChannelMemory => ({
  channelId: dto.channel_id,
  approvedTitlePatterns: dto.memory?.approved_title_patterns ?? [],
  rejectedTitlePatterns: dto.memory?.rejected_title_patterns ?? [],
  thumbnailRules: dto.memory?.thumbnail_rules ?? {},
  bannedPhrases: dto.memory?.banned_phrases ?? [],
  preferredPhrases: dto.memory?.preferred_phrases ?? [],
  compliancePreferences: dto.memory?.compliance_preferences ?? {},
  narratorStyle: dto.memory?.narrator_style ?? {},
  visualStyle: dto.memory?.visual_style ?? {},
  audienceObjections: dto.memory?.audience_objections ?? [],
  bestPerformingPatterns: dto.memory?.best_performing_patterns ?? [],
  worstPerformingPatterns: dto.memory?.worst_performing_patterns ?? [],
  freeformMemoryNotes: dto.memory?.freeform_memory_notes ?? []
});


const mapIdeaDto = (dto: BackendContentIdea): ContentIdea => ({
  id: dto.id,
  organizationId: dto.organization_id,
  workspaceId: dto.workspace_id,
  channelId: dto.channel_id,
  title: dto.title,
  summary: dto.summary ?? '',
  contentPillar: dto.content_pillar,
  status: dto.status,
  createdAt: dto.created_at,
  updatedAt: dto.updated_at
});
const mapProjectDto = (dto: BackendVideoProject): VideoProject => ({ id: dto.id, title: dto.title, topic: '', description: '', channel: dto.channel_id, language: '', targetAudience: '', status: dto.status, aiCostUsd: dto.ai_cost_usd ?? 0, youtubeQuotaUsed: dto.youtube_quota_used ?? 0, createdAt: dto.created_at, updatedAt: dto.updated_at, overview: dto.overview ?? '', research: dto.research ?? '', script: dto.script ?? '', seo: dto.seo ?? '', approvalNote: dto.approval_note, compliance: { score: dto.compliance?.score ?? 0, riskLevel: dto.compliance?.risk_level ?? 'low', blockingIssues: dto.compliance?.blocking_issues ?? [], recommendations: dto.compliance?.recommendations ?? [] }, workflowEvents: (dto.workflow_events ?? []).map((event) => ({ id: event.id, timestamp: new Date().toISOString(), actor: event.payload?.actor ? String(event.payload.actor) : 'system', event: event.event_type })), analytics: { estimatedCtr: dto.analytics?.estimated_ctr ?? 0, projectedViews: dto.analytics?.projected_views ?? 0 } });

const mapIdeaResearchReport = (dto: any): IdeaResearchReport => ({
  id: dto.id,
  ideaId: dto.idea_id,
  summary: dto.summary ?? '',
  recommendation: (dto.recommendation ?? 'needs_more_research') as IdeaResearchRecommendation,
  scores: {
    demandScore: dto.scores?.demand_score ?? 0,
    competitionScore: dto.scores?.competition_score ?? 0,
    evidenceScore: dto.scores?.evidence_score ?? 0
  },
  missingEvidence: dto.missing_evidence ?? [],
  genericRisks: dto.generic_risks ?? [],
  recommendedNextAction: dto.recommended_next_action ?? '',
  createdAt: dto.created_at
});
const mapAnalyticsDto = (dto: BackendAnalyticsSnapshot): AnalyticsSnapshot => ({ id: dto.id, videoProjectId: dto.video_project_id, channelId: dto.channel_id, youtubeVideoId: dto.youtube_video_id, views: dto.views, watchTimeMinutes: dto.watch_time_minutes, averageViewDuration: dto.average_view_duration, ctr: dto.ctr, likes: dto.likes, comments: dto.comments, subscribersGained: dto.subscribers_gained, estimatedRevenue: dto.estimated_revenue, snapshotAt: dto.snapshot_at });

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
  } finally { clearTimeout(timeoutId); onLoadingChange?.(false); }
}

export const apiClient = { buildApiUrl,
  async listProjects(filters?: { status?: ProjectStatus; channel?: string; onLoadingChange?: (isLoading: boolean) => void }) { const response = await apiRequest<ProjectsCollectionResponse>(backendApiAdapter.paths.projects, { query: backendApiAdapter.toListProjectsQuery(filters), onLoadingChange: filters?.onLoadingChange }); return response.items.map(mapProjectDto); },
  async getProject(id: string, options?: { onLoadingChange?: (isLoading: boolean) => void }) { const project = await apiRequest<BackendVideoProject>(backendApiAdapter.paths.projectById(id), { onLoadingChange: options?.onLoadingChange }); return mapProjectDto(project); },
  async createProject(input: CreateProjectInput, options?: { onLoadingChange?: (isLoading: boolean) => void }) { const project = await apiRequest<BackendVideoProject>(backendApiAdapter.paths.projects, { method: 'POST', body: backendApiAdapter.toCreateProjectBody(input), onLoadingChange: options?.onLoadingChange }); return mapProjectDto(project); },
  async listAnalytics(id: string, options?: { onLoadingChange?: (isLoading: boolean) => void }): Promise<AnalyticsSnapshot[]> { const rows = await apiRequest<BackendAnalyticsSnapshot[]>(backendApiAdapter.paths.projectAnalytics(id), { onLoadingChange: options?.onLoadingChange }); return rows.map(mapAnalyticsDto); },
  async setApproval(id: string, approve: boolean, note?: string, options?: { onLoadingChange?: (isLoading: boolean) => void }) { const path = approve ? backendApiAdapter.paths.projectApprove(id) : backendApiAdapter.paths.projectReject(id); const project = await apiRequest<BackendVideoProject>(path, { method: 'POST', body: backendApiAdapter.toApprovalBody(approve, note), onLoadingChange: options?.onLoadingChange }); return mapProjectDto(project); },
  async listChannels(options?: { limit?: number; offset?: number; onLoadingChange?: (isLoading: boolean) => void }) { const response = await apiRequest<ChannelsCollectionResponse>(backendApiAdapter.paths.channels, { query: { limit: options?.limit, offset: options?.offset }, onLoadingChange: options?.onLoadingChange }); return response.items.map(mapChannelDto); },
  async getChannel(id: string, options?: { onLoadingChange?: (isLoading: boolean) => void }) { return mapChannelDto(await apiRequest<BackendChannel>(backendApiAdapter.paths.channelById(id), { onLoadingChange: options?.onLoadingChange })); },
  async createChannel(input: CreateChannelInput, options?: { onLoadingChange?: (isLoading: boolean) => void }) { return mapChannelDto(await apiRequest<BackendChannel>(backendApiAdapter.paths.channels, { method: 'POST', body: backendApiAdapter.toCreateChannelBody(input), onLoadingChange: options?.onLoadingChange })); },
  async updateChannel(id: string, input: UpdateChannelInput, options?: { onLoadingChange?: (isLoading: boolean) => void }) { return mapChannelDto(await apiRequest<BackendChannel>(backendApiAdapter.paths.channelById(id), { method: 'PATCH', body: backendApiAdapter.toPatchChannelBody(input), onLoadingChange: options?.onLoadingChange })); },
  async deleteChannel(id: string, options?: { onLoadingChange?: (isLoading: boolean) => void }) { await apiRequest<void>(backendApiAdapter.paths.channelById(id), { method: 'DELETE', onLoadingChange: options?.onLoadingChange }); },
  async getChannelMemory(id: string, options?: { onLoadingChange?: (isLoading: boolean) => void }) { return mapChannelMemory(await apiRequest<BackendChannelMemoryOut>(backendApiAdapter.paths.channelMemory(id), { onLoadingChange: options?.onLoadingChange })); },
  async updateChannelMemory(id: string, input: ChannelMemoryInput, options?: { onLoadingChange?: (isLoading: boolean) => void }) { return mapChannelMemory(await apiRequest<BackendChannelMemoryOut>(backendApiAdapter.paths.channelMemory(id), { method: 'PATCH', body: backendApiAdapter.toChannelMemoryBody(input), onLoadingChange: options?.onLoadingChange })); },
  async runNicheAnalysis(id: string, notes = '', options?: { onLoadingChange?: (isLoading: boolean) => void }) { return mapNicheReport(await apiRequest<any>(backendApiAdapter.paths.nicheAnalyze(id), { method: 'POST', body: { notes }, onLoadingChange: options?.onLoadingChange })); },
  async listNicheReports(id: string, options?: { onLoadingChange?: (isLoading: boolean) => void }) { const response = await apiRequest<{ items: any[] }>(backendApiAdapter.paths.nicheReports(id), { onLoadingChange: options?.onLoadingChange }); return response.items.map(mapNicheReport); },

  async listIdeas(filters?: { status?: ContentIdeaStatus; contentPillar?: string; query?: string; onLoadingChange?: (isLoading: boolean) => void }) {
    const response = await apiRequest<{ items: BackendContentIdea[] }>(backendApiAdapter.paths.ideas, { query: backendApiAdapter.toListIdeasQuery(filters), onLoadingChange: filters?.onLoadingChange });
    return response.items.map(mapIdeaDto);
  },
  async getIdea(id: string, options?: { onLoadingChange?: (isLoading: boolean) => void }) {
    return mapIdeaDto(await apiRequest<BackendContentIdea>(backendApiAdapter.paths.ideaById(id), { onLoadingChange: options?.onLoadingChange }));
  },
  async createIdea(input: CreateContentIdeaInput, options?: { onLoadingChange?: (isLoading: boolean) => void }) {
    return mapIdeaDto(await apiRequest<BackendContentIdea>(backendApiAdapter.paths.ideas, { method: 'POST', body: backendApiAdapter.toCreateIdeaBody(input), onLoadingChange: options?.onLoadingChange }));
  },
  async updateIdea(id: string, input: UpdateContentIdeaInput, options?: { onLoadingChange?: (isLoading: boolean) => void }) {
    return mapIdeaDto(await apiRequest<BackendContentIdea>(backendApiAdapter.paths.ideaById(id), { method: 'PATCH', body: backendApiAdapter.toUpdateIdeaBody(input), onLoadingChange: options?.onLoadingChange }));
  },
  async updateIdeaStatus(id: string, status: ContentIdeaStatus, options?: { onLoadingChange?: (isLoading: boolean) => void }) {
    return mapIdeaDto(await apiRequest<BackendContentIdea>(backendApiAdapter.paths.ideaStatus(id), { method: 'PATCH', body: { status }, onLoadingChange: options?.onLoadingChange }));
  },

  async analyzeIdeaResearch(id: string, options?: { onLoadingChange?: (isLoading: boolean) => void }) {
    return mapIdeaResearchReport(await apiRequest<any>(backendApiAdapter.paths.ideaResearchAnalyze(id), { method: 'POST', onLoadingChange: options?.onLoadingChange }));
  },
  async getLatestIdeaResearch(id: string, options?: { onLoadingChange?: (isLoading: boolean) => void }) {
    return mapIdeaResearchReport(await apiRequest<any>(backendApiAdapter.paths.ideaResearchLatest(id), { onLoadingChange: options?.onLoadingChange }));
  },
  async listIdeaResearchReports(id: string, options?: { onLoadingChange?: (isLoading: boolean) => void }) {
    const response = await apiRequest<{ items: any[] }>(backendApiAdapter.paths.ideaResearchReports(id), { onLoadingChange: options?.onLoadingChange });
    return response.items.map(mapIdeaResearchReport);
  },
};


const mapNicheReport = (dto: any): NicheReport => ({ id: dto.id, channelId: dto.channel_id, summary: dto.summary, scoreExplanations: dto.score_explanations ?? {}, strengths: dto.strengths ?? [], weaknesses: dto.weaknesses ?? [], risks: dto.risks ?? [], recommendedPositioning: dto.recommended_positioning ?? "", contentPillarSuggestions: dto.content_pillar_suggestions ?? [], differentiationOpportunities: dto.differentiation_opportunities ?? [], complianceNotes: dto.compliance_notes ?? [], nextActions: dto.next_actions ?? [], scores: { demandScore: dto.scores?.demand_score ?? 0, competitionScore: dto.scores?.competition_score ?? 0, originalityPotential: dto.scores?.originality_potential ?? 0, productionDifficulty: dto.scores?.production_difficulty ?? 0, monetizationPotential: dto.scores?.monetization_potential ?? 0, complianceRisk: dto.scores?.compliance_risk ?? 0, longTermDepth: dto.scores?.long_term_depth ?? 0, overallScore: dto.scores?.overall_score ?? 0 }, createdAt: dto.created_at });
