# Workflow Engine

## Cel
Workflow prowadzi zespół przez powtarzalny proces produkcji wideo z kontrolą jakości i approval gate.

## Sekwencja kroków
1. `create_video_project`
2. `generate_research`
3. `generate_script`
4. `generate_seo`
5. `run_compliance_check`
6. `request_human_approval`
7. `wait_for_approval`
8. `schedule_or_publish`
9. `sync_analytics`

## Jak działa start
- `start_workflow` tworzy `WorkflowRun`.
- Dla każdego kroku tworzy `WorkflowStep` i event `workflow.step_created`.
- Na `wait_for_approval` workflow zatrzymuje się i ustawia projekt na `awaiting_review`.

## Jak działa approval
- **approve**: backend sprawdza compliance report. Jeśli są `blocking_issues`, approval jest blokowany.
- **reject**: status `rejected` i event odrzucenia.
- **needs_changes**: status `needs_changes`, pętla feedbackowa.

## Dlaczego to ważne biznesowo
- Ogranicza publikacje wysokiego ryzyka.
- Daje jasny ownership decyzji.
- Uspójnia pracę wielu osób w jednym flow.
