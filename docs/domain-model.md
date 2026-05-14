# Domain Model

## Multi-tenant hierarchy
1. **Organization**
2. **Workspace**
3. **Channel**
4. **VideoProject**

To jest rdzeń separacji danych i limitów planowych.

## Core entities
- `VideoProject` — jednostka pracy od pomysłu do publikacji.
- `VideoIdea`, `ScriptDraft`, `SEORecommendation` — artefakty contentowe.
- `ComplianceReport` — wynik oceny ryzyka.
- `WorkflowRun`, `WorkflowStep`, `WorkflowEvent` — orkiestracja i audit trail.
- `ApprovalDecision` — decyzja człowieka: approved/rejected/needs_changes.
- `PublishingPlan` — plan publikacji + status i metadane YouTube.
- `LLMCostLedgerEntry`, `YouTubeQuotaLedgerEntry` — rozliczalność kosztów i quota.
- `AnalyticsSnapshot` — dane wynikowe post-publikacyjne.

## Lifecycle status (VideoProject)
`draft -> researching -> script_generating -> seo_generating -> compliance_checking -> awaiting_review -> approved/rejected/needs_changes -> scheduled/published -> completed`.

## Modeling principles
- Statusy jako enumy, żeby wymuszać spójny cykl życia.
- Zdarzenia i decyzje jako osobne tabele dla audytu.
- Ledgery kosztowe jako append-only source of truth do raportów usage.
