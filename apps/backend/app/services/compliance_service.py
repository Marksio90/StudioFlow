from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.db.enums import ComplianceRiskLevel
from app.services.repetitive_content_detector import ProjectContent, RepetitiveContentDetector

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
    def __init__(self, repetitive_detector: RepetitiveContentDetector | None = None) -> None:
        self.repetitive_detector = repetitive_detector or RepetitiveContentDetector()

    def evaluate(self, payload: ComplianceInput) -> ComplianceReport:
        m = payload.metadata
        repetitive = self._evaluate_repetitive_content(m)
        report = ComplianceReport(
            video_project_id=payload.video_project_id,
            score=int(m.get("score", 80)),
            risk_level=ComplianceRiskLevel(m.get("risk_level", "low")),
            requires_ai_disclosure=bool(m.get("requires_ai_disclosure", False)),
            disclosure_decision_missing=payload.disclosure_decision_missing,
            ai_disclosure_risk=m.get("ai_disclosure_risk", "low"),
            inauthentic_content_risk=m.get("inauthentic_content_risk", "low"),
            repetitive_content_risk=repetitive["risk_level"],
            copyright_risk=m.get("copyright_risk", "low"),
            sensitive_claims_risk=m.get("sensitive_claims_risk", "low"),
            clickbait_risk=m.get("clickbait_risk", "low"),
            asset_license_risk=m.get("asset_license_risk", "low"),
            synthetic_media_realism_risk=m.get("synthetic_media_realism_risk", "low"),
            reasons=[*m.get("reasons", []), *repetitive["reasons"]],
            recommendations=[*m.get("recommendations", []), *repetitive["recommendations"]],
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

    def _evaluate_repetitive_content(self, metadata: dict) -> dict:
        current = metadata.get("current_project")
        previous = metadata.get("previous_projects", [])
        if not current:
            risk = metadata.get("repetitive_content_risk", "low")
            return {"risk_level": risk, "reasons": [], "recommendations": []}
        result = self.repetitive_detector.detect(
            ProjectContent(**current),
            [ProjectContent(**item) for item in previous],
        )
        return {
            "risk_level": result.risk_level,
            "reasons": [f"Repetitive similarity={result.overall_similarity}", *result.reasons],
            "recommendations": result.recommendations,
        }
