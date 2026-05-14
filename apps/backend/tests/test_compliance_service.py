from uuid import uuid4

from app.db.enums import ComplianceRiskLevel
from app.services.compliance_service import ComplianceInput, ComplianceService


def test_low_risk_score_mapping():
    report = ComplianceService().evaluate(ComplianceInput(video_project_id=uuid4(), metadata={"score": 85}))
    assert report.risk_level == ComplianceRiskLevel.low


def test_medium_risk_score_mapping():
    report = ComplianceService().evaluate(ComplianceInput(video_project_id=uuid4(), metadata={"score": 55}))
    assert report.risk_level == ComplianceRiskLevel.medium


def test_high_risk_score_mapping():
    report = ComplianceService().evaluate(ComplianceInput(video_project_id=uuid4(), metadata={"score": 10}))
    assert report.risk_level == ComplianceRiskLevel.high


def test_blocked_when_blocking_policy_matches():
    report = ComplianceService().evaluate(
        ComplianceInput(
            video_project_id=uuid4(),
            metadata={"score": 90, "requires_ai_disclosure": True, "asset_license_risk": "high"},
            disclosure_decision_missing=True,
        )
    )
    assert report.risk_level == ComplianceRiskLevel.blocked
    assert "asset_license_risk_high" in report.blocking_issues
    assert "missing_ai_disclosure_decision" in report.blocking_issues
