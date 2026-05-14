import { AnalyticsSnapshot, CreateProjectInput, VideoProject, ProjectStatus } from './types';

const STORAGE_KEY = 'studioflow_projects_v1';

const seed: VideoProject[] = [
  {
    id: 'p_001',
    title: 'How AI Edits Shorts Faster',
    topic: 'AI video editing workflow',
    description: 'Explainer on automating clips and subtitles.',
    channel: 'StudioFlow Lab',
    language: 'English',
    targetAudience: 'YouTube creators',
    status: 'awaiting_review',
    aiCostUsd: 42.5,
    youtubeQuotaUsed: 120,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    overview: 'Automated pipeline from idea to upload package.',
    research: 'Top pain point: turnaround time and consistency.',
    script: 'Hook → pain points → demo → CTA',
    seo: 'Keywords: ai video editing, creator automation',
    approvalNote: '',
    compliance: {
      score: 82,
      riskLevel: 'medium',
      blockingIssues: ['Missing source attribution in segment 2'],
      recommendations: ['Add source links in description', 'Avoid unverified benchmark claims']
    },
    workflowEvents: [
      { id: 'e1', timestamp: new Date().toISOString(), actor: 'system', event: 'Project created' }
    ],
    analytics: { estimatedCtr: 5.1, projectedViews: 24000 }
  }
];

const wait = (ms = 450) => new Promise((r) => setTimeout(r, ms));

const hasWindow = typeof window !== 'undefined';

function getProjects(): VideoProject[] {
  if (!hasWindow) return seed;
  const raw = window.localStorage.getItem(STORAGE_KEY);
  if (!raw) {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(seed));
    return seed;
  }
  return JSON.parse(raw) as VideoProject[];
}

function setProjects(projects: VideoProject[]) {
  if (hasWindow) window.localStorage.setItem(STORAGE_KEY, JSON.stringify(projects));
}

export const apiClient = {
  async listProjects(filters?: { status?: ProjectStatus; channel?: string }) {
    await wait();
    let rows = getProjects();
    if (filters?.status) rows = rows.filter((p) => p.status === filters.status);
    if (filters?.channel) rows = rows.filter((p) => p.channel === filters.channel);
    return rows;
  },
  async getProject(id: string) {
    await wait();
    const found = getProjects().find((p) => p.id === id);
    if (!found) throw new Error('Project not found');
    return found;
  },
  async createProject(input: CreateProjectInput) {
    await wait();
    const projects = getProjects();
    const now = new Date().toISOString();
    const project: VideoProject = {
      id: `p_${Math.random().toString(36).slice(2, 8)}`,
      ...input,
      status: 'draft',
      aiCostUsd: 0,
      youtubeQuotaUsed: 0,
      createdAt: now,
      updatedAt: now,
      overview: input.description,
      research: 'Pending research generation',
      script: 'Pending script generation',
      seo: 'Pending SEO generation',
      compliance: { score: 100, riskLevel: 'low', blockingIssues: [], recommendations: [] },
      workflowEvents: [{ id: `e_${Date.now()}`, timestamp: now, actor: 'user', event: 'Project created' }],
      analytics: { estimatedCtr: 0, projectedViews: 0 }
    };
    const next = [project, ...projects];
    setProjects(next);
    return project;
  },
  async listAnalytics(id: string): Promise<AnalyticsSnapshot[]> {
    await wait();
    const p = await this.getProject(id);
    return [{
      id: `a_${id}`,
      video_project_id: id,
      channel_id: p.channel,
      youtube_video_id: `yt_${id}`,
      views: p.analytics.projectedViews,
      watch_time_minutes: 1200,
      average_view_duration: 145,
      ctr: p.analytics.estimatedCtr,
      likes: 100,
      comments: 12,
      subscribers_gained: 8,
      estimated_revenue: 75.5,
      snapshot_at: new Date().toISOString()
    }];
  },
  async setApproval(id: string, approve: boolean, note?: string) {
    await wait();
    const projects = getProjects();
    const idx = projects.findIndex((p) => p.id === id);
    if (idx < 0) throw new Error('Project not found');
    const now = new Date().toISOString();
    const updated = {
      ...projects[idx],
      status: approve ? 'approved' : 'rejected' as ProjectStatus,
      approvalNote: note,
      updatedAt: now,
      workflowEvents: [
        { id: `e_${Date.now()}`, timestamp: now, actor: 'reviewer', event: approve ? 'Approved' : 'Rejected' },
        ...projects[idx].workflowEvents
      ]
    };
    projects[idx] = updated;
    setProjects(projects);
    return updated;
  }
};
