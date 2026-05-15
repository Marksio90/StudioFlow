import type { components } from '../../../packages/shared/src/backend-api';

export type ProjectStatus = components['schemas']['VideoProjectStatus'];

export type RiskLevel = components['schemas']['ComplianceRiskLevel'];

export type ContentIdeaStatus =
  | 'ideas'
  | 'research'
  | 'angle_review'
  | 'script_draft'
  | 'compliance_review'
  | 'ready'
  | 'published'
  | 'analyzed';

export interface ContentIdea {
  id: string;
  organizationId: string;
  workspaceId: string;
  channelId: string;
  title: string;
  summary: string;
  contentPillar: string;
  status: ContentIdeaStatus;
  createdAt: string;
  updatedAt: string;
}

export interface CreateContentIdeaInput {
  title: string;
  summary?: string;
  contentPillar: string;
}

export interface UpdateContentIdeaInput {
  title?: string;
  summary?: string;
  contentPillar?: string;
}

export type IdeaResearchRecommendation =
  | 'proceed'
  | 'proceed_with_caution'
  | 'do_not_proceed'
  | 'needs_more_research';

export interface IdeaResearchScores {
  demandScore: number;
  competitionScore: number;
  evidenceScore: number;
}

export interface IdeaResearchReport {
  id: string;
  ideaId: string;
  summary: string;
  recommendation: IdeaResearchRecommendation;
  scores: IdeaResearchScores;
  missingEvidence: string[];
  genericRisks: string[];
  recommendedNextAction: string;
  createdAt: string;
}

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

export interface Channel {
  id: string;
  organizationId: string;
  workspaceId: string;
  name: string;
  youtubeChannelId: string;
  createdAt: string;
  updatedAt: string;
}

export interface CreateChannelInput { name: string; youtubeChannelId: string; }
export interface UpdateChannelInput { name?: string; youtubeChannelId?: string; }

export interface ChannelMemory {
  channelId: string;
  approvedTitlePatterns: string[];
  rejectedTitlePatterns: string[];
  thumbnailRules: Record<string, unknown>;
  bannedPhrases: string[];
  preferredPhrases: string[];
  compliancePreferences: Record<string, unknown>;
  narratorStyle: Record<string, unknown>;
  visualStyle: Record<string, unknown>;
  audienceObjections: string[];
  bestPerformingPatterns: string[];
  worstPerformingPatterns: string[];
  freeformMemoryNotes: string[];
}

export type ChannelMemoryInput = Omit<ChannelMemory, 'channelId'>;


export interface NicheScores {
  demandScore: number; competitionScore: number; originalityPotential: number; productionDifficulty: number; monetizationPotential: number; complianceRisk: number; longTermDepth: number; overallScore: number;
}

export interface NicheReport {
  id: string; channelId: string; summary: string; scoreExplanations: Record<string,string>; strengths: string[]; weaknesses: string[]; risks: string[]; recommendedPositioning: string; contentPillarSuggestions: string[]; differentiationOpportunities: string[]; complianceNotes: string[]; nextActions: string[]; scores: NicheScores; createdAt: string;
}
