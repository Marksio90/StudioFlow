export type ProjectStatus =
  | 'draft'
  | 'researching'
  | 'scripting'
  | 'awaiting_review'
  | 'approved'
  | 'rejected'
  | 'published';

export type RiskLevel = 'low' | 'medium' | 'high';

export interface ComplianceReport {
  score: number;
  riskLevel: RiskLevel;
  blockingIssues: string[];
  recommendations: string[];
}

export interface WorkflowEvent {
  id: string;
  timestamp: string;
  actor: string;
  event: string;
}

export interface VideoProject {
  id: string;
  title: string;
  topic: string;
  description: string;
  channel: string;
  language: string;
  targetAudience: string;
  status: ProjectStatus;
  aiCostUsd: number;
  youtubeQuotaUsed: number;
  createdAt: string;
  updatedAt: string;
  overview: string;
  research: string;
  script: string;
  seo: string;
  approvalNote?: string;
  compliance: ComplianceReport;
  workflowEvents: WorkflowEvent[];
  analytics: { estimatedCtr: number; projectedViews: number };
}

export interface CreateProjectInput {
  title: string;
  topic: string;
  description: string;
  channel: string;
  language: string;
  targetAudience: string;
}


export interface AnalyticsSnapshot {
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
