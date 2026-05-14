# AI Agents

## Rola agentów
Agenci wspierają etapy research/script/SEO/compliance/performance. Generują propozycje, ale decyzje finalne pozostają po stronie człowieka.

## Dostępni agenci
- `ResearchAgent`
- `ScriptAgent`
- `SEOAgent`
- `ComplianceAgent`
- (oraz modele wejścia/wyjścia pod performance/classification/summarization)

## Kontrakt działania
- Każdy agent ma typowane input/output (Pydantic).
- `BaseAgent` obsługuje retry (`max_attempts`).
- Błędy kończą się `AgentExecutionError` po wyczerpaniu retry.

## Model routing
`ModelRouter` wybiera model per task przez ENV, np.:
- `LLM_RESEARCH_MODEL`
- `LLM_SCRIPT_MODEL`
- `LLM_SEO_MODEL`
- `LLM_COMPLIANCE_MODEL`

## Cost tracking
`TrackedLLMClient` zapisuje metryki:
- task_type, model, tokeny in/out,
- estymowany koszt,
- latency,
- request hash,
- kontekst tenant/project/workflow.

To podstawa kontroli kosztów i rozliczeń planowych.
