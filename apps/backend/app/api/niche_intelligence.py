from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.api.channels import _get_channel
from app.api.deps import Identity, get_correlation_id, get_db_session, require_action
from app.db.models import NicheIntelligenceReport
from app.schemas.niche_intelligence import NicheAnalyzeRequest, NicheIntelligenceReportListOut, NicheIntelligenceReportOut
from app.services.ai_provider import MockLLMProvider
from app.services.niche_intelligence_service import NicheIntelligenceService
from app.services.prompt_registry import build_default_prompt_registry

router = APIRouter(prefix='/api/v1/channels/{channel_id}/niche', tags=['niche-intelligence'])


def _to_out(row: NicheIntelligenceReport) -> NicheIntelligenceReportOut:
    return NicheIntelligenceReportOut(
        id=row.id, channel_id=row.channel_id, summary=row.summary, score_explanations=row.score_explanations,
        strengths=row.strengths, weaknesses=row.weaknesses, risks=row.risks, recommended_positioning=row.recommended_positioning,
        content_pillar_suggestions=row.content_pillar_suggestions, differentiation_opportunities=row.differentiation_opportunities,
        compliance_notes=row.compliance_notes, next_actions=row.next_actions, scores=row.scores, created_at=row.created_at
    )


@router.post('/analyze', response_model=NicheIntelligenceReportOut)
async def analyze_channel_niche(channel_id: UUID, payload: NicheAnalyzeRequest, correlation_id: str = Depends(get_correlation_id), session=Depends(get_db_session), identity: Identity = Depends(require_action('write', 'channels'))):
    await _get_channel(channel_id, correlation_id, identity, session)
    service = NicheIntelligenceService(provider=MockLLMProvider(), prompt_registry=build_default_prompt_registry())
    report = await service.analyze(session, channel_id=channel_id, notes=payload.notes)
    return _to_out(report)


@router.get('/reports', response_model=NicheIntelligenceReportListOut)
async def list_niche_reports(channel_id: UUID, correlation_id: str = Depends(get_correlation_id), session=Depends(get_db_session), identity: Identity = Depends(require_action('read', 'channels'))):
    await _get_channel(channel_id, correlation_id, identity, session)
    rows = (await session.execute(select(NicheIntelligenceReport).where(NicheIntelligenceReport.channel_id == channel_id).order_by(NicheIntelligenceReport.created_at.desc()))).scalars().all()
    return {'items': [_to_out(r) for r in rows]}


@router.get('/reports/{report_id}', response_model=NicheIntelligenceReportOut)
async def get_niche_report(channel_id: UUID, report_id: UUID, correlation_id: str = Depends(get_correlation_id), session=Depends(get_db_session), identity: Identity = Depends(require_action('read', 'channels'))):
    await _get_channel(channel_id, correlation_id, identity, session)
    row = (await session.execute(select(NicheIntelligenceReport).where(NicheIntelligenceReport.id == report_id, NicheIntelligenceReport.channel_id == channel_id))).scalar_one()
    return _to_out(row)
