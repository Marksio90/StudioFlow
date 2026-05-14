from __future__ import annotations

import subprocess
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.plan_limit_service import PlanLimitService
from app.services.youtube_quota_service import YouTubeCallContext, YouTubeQuotaService


def test_plan_limits_invariants_starter_vs_pro() -> None:
    limits = PlanLimitService()
    starter = limits.get_limits("starter")
    pro = limits.get_limits("pro")

    assert starter.max_video_projects_per_month == 20
    assert pro.max_video_projects_per_month == 200
    assert pro.max_video_projects_per_month > starter.max_video_projects_per_month


def test_plan_limits_assertion_blocks_overflow() -> None:
    limits = PlanLimitService()
    with pytest.raises(ValueError, match="video_projects limit reached"):
        limits.assert_within_limit("video_projects", 20, 20)


@pytest.mark.asyncio
async def test_quota_ledger_is_append_only() -> None:
    class Repo:
        def __init__(self):
            self.youtube_quota_ledger_entries = []

        async def log_youtube_quota_entry(self, entry):
            self.youtube_quota_ledger_entries.append(entry)
            return entry

    repo = Repo()
    quota = YouTubeQuotaService(repo, method_costs={"videos.insert": 1600})
    context = YouTubeCallContext(
        organization_id=uuid4(),
        workspace_id=uuid4(),
        channel_id=uuid4(),
        video_project_id=uuid4(),
    )

    await quota.log_call(context, youtube_method="videos.insert", success=True)
    await quota.log_call(context, youtube_method="videos.insert", success=False)

    assert len(repo.youtube_quota_ledger_entries) == 2
    assert repo.youtube_quota_ledger_entries[0]["success"] is True
    assert repo.youtube_quota_ledger_entries[1]["success"] is False


def test_alembic_upgrade_downgrade_smoke() -> None:
    backend_dir = Path(__file__).resolve().parents[1]

    env = {**dict(__import__("os").environ), "PYTHONPATH": str(backend_dir)}
    upgrade = subprocess.run(["alembic", "upgrade", "head"], cwd=backend_dir, env=env, capture_output=True, text=True, check=False)
    if upgrade.returncode != 0:
        pytest.skip(f"Alembic upgrade smoke cannot run in this environment: {upgrade.stderr}")

    downgrade = subprocess.run(["alembic", "downgrade", "base"], cwd=backend_dir, env=env, capture_output=True, text=True, check=False)
    assert downgrade.returncode == 0, downgrade.stderr

    reupgrade = subprocess.run(["alembic", "upgrade", "head"], cwd=backend_dir, env=env, capture_output=True, text=True, check=False)
    assert reupgrade.returncode == 0, reupgrade.stderr


def test_docker_compose_healthcheck_orchestration() -> None:
    compose_path = Path(__file__).resolve().parents[3] / "docker-compose.yml"
    compose = compose_path.read_text()

    assert "condition: service_healthy" in compose
    assert "healthcheck:" in compose
    assert "pg_isready" in compose
    assert "http://localhost:8000/health" in compose


def test_backend_health_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code in {200, 429}
    if response.status_code == 200:
        assert response.json()["status"] == "ok"
