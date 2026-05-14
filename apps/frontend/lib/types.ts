import type { components } from '../../../packages/shared/src/backend-api';

export type ProjectStatus = components['schemas']['VideoProjectStatus'];

export type RiskLevel = components['schemas']['ComplianceRiskLevel'];

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
  videoProjectId: string;
  channelId: string;
  youtubeVideoId: string;
  views: number;
  watchTimeMinutes: number;
  averageViewDuration: number;
  ctr: number;
  likes: number;
  comments: number;
  subscribersGained: number;
  estimatedRevenue: number;
  snapshotAt: string;
}
