from enum import Enum


class VideoProjectStatus(str, Enum):
    draft = "draft"
    researching = "researching"
    script_generating = "script_generating"
    seo_generating = "seo_generating"
    compliance_checking = "compliance_checking"
    awaiting_review = "awaiting_review"
    approved = "approved"
    rejected = "rejected"
    needs_changes = "needs_changes"
    scheduled = "scheduled"
    published = "published"
    analytics_pending = "analytics_pending"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class ComplianceRiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    blocked = "blocked"


class ApprovalStatus(str, Enum):
    awaiting_review = "awaiting_review"
    approved = "approved"
    rejected = "rejected"
    needs_changes = "needs_changes"
