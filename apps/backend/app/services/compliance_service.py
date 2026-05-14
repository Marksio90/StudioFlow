from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.db.enums import ComplianceRiskLevel

RiskTier = Literal["low", "medium", "high"]


class ComplianceInput(BaseModel):
    video_project_id: UUID
    script: str = ""
    metadata: dict = Field(default_factory=dict)
    disclosure_decision_missing: bool = False


class ComplianceReport(BaseModel):
    video_project_id: UUID
    score: int = Field(ge=0, le=100)
    risk_level: ComplianceRiskLevel
    requires_ai_disclosure: bool
    disclosure_decision_missing: bool
    ai_disclosure_risk: RiskTier
    inauthentic_content_risk: RiskTier
    repetitive_content_risk: RiskTier
    copyright_risk: RiskTier
    sensitive_claims_risk: RiskTier
    clickbait_risk: RiskTier
    asset_license_risk: RiskTier
    synthetic_media_realism_risk: RiskTier
    reasons: list[str]
    recommendations: list[str]
    blocking_issues: list[str]


class ComplianceService:
    def evaluate(self, payload: ComplianceInput) -> ComplianceReport:
        m = payload.metadata
        report = ComplianceReport(
            video_project_id=payload.video_project_id,
            score=int(m.get("score", 80)),
            risk_level=ComplianceRiskLevel(m.get("risk_level", "low")),
            requires_ai_disclosure=bool(m.get("requires_ai_disclosure", False)),
            disclosure_decision_missing=payload.disclosure_decision_missing,
            ai_disclosure_risk=m.get("ai_disclosure_risk", "low"),
            inauthentic_content_risk=m.get("inauthentic_content_risk", "low"),
            repetitive_content_risk=m.get("repetitive_content_risk", "low"),
            copyright_risk=m.get("copyright_risk", "low"),
            sensitive_claims_risk=m.get("sensitive_claims_risk", "low"),
            clickbait_risk=m.get("clickbait_risk", "low"),
            asset_license_risk=m.get("asset_license_risk", "low"),
            synthetic_media_realism_risk=m.get("synthetic_media_realism_risk", "low"),
            reasons=m.get("reasons", []),
            recommendations=m.get("recommendations", []),
            blocking_issues=[],
        )
        report.risk_level = self._normalize_risk_level(report.score, report.risk_level)
        report.blocking_issues = self._blocking_issues(report)
        if report.blocking_issues:
            report.risk_level = ComplianceRiskLevel.blocked
        return report

    def _normalize_risk_level(self, score: int, current: ComplianceRiskLevel) -> ComplianceRiskLevel:
        if current == ComplianceRiskLevel.blocked:
            return current
        if score <= 39:
            return ComplianceRiskLevel.high
        if score <= 69:
            return ComplianceRiskLevel.medium
        return ComplianceRiskLevel.low

    def _blocking_issues(self, report: ComplianceReport) -> list[str]:
        issues: list[str] = []
        if report.risk_level == ComplianceRiskLevel.blocked:
            issues.append("risk_level_blocked")
        if report.copyright_risk == "high":
            issues.append("copyright_risk_high")
        if report.asset_license_risk == "high":
            issues.append("asset_license_risk_high")
        if report.repetitive_content_risk == "high":
            issues.append("repetitive_content_risk_high")
        if report.requires_ai_disclosure and report.disclosure_decision_missing:
            issues.append("missing_ai_disclosure_decision")
        return issues
