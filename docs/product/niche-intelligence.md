# Niche Intelligence

Niche Intelligence analyzes a channel niche using existing channel fields, channel memory, and optional user notes.
It produces validated scores and actionable recommendations.

## Scores
- demand_score
- competition_score
- originality_potential
- production_difficulty
- monetization_potential
- compliance_risk
- long_term_depth
- overall_score

## API
- `POST /api/v1/channels/{channel_id}/niche/analyze`
- `GET /api/v1/channels/{channel_id}/niche/reports`
- `GET /api/v1/channels/{channel_id}/niche/reports/{report_id}`
