# LLM Cost Control

## Założenie
Kontrola kosztów AI jest funkcją produktu, nie "afterthoughtem".

## Mechanizm
1. Każde wywołanie agenta przechodzi przez `TrackedLLMClient`.
2. Wyliczane są tokeny wejścia/wyjścia i estymowany koszt.
3. Zdarzenie kosztowe trafia do trackera/ledgera.
4. `UsageService` agreguje miesięczne zużycie per organization.

## Limity planowe (przykładowe)
- Starter: `max_ai_cost_usd_per_month = 10.0`
- Pro: `max_ai_cost_usd_per_month = 200.0`
- Agency: bez hard limitów

## Dobre praktyki productowe
- routing tańszych modeli dla etapów o niskiej krytyczności,
- retry policy z limitem prób,
- alerts przy zbliżaniu się do limitu,
- dashboard koszt per workflow i per klient.
