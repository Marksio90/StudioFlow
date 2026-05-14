# YouTube API & Quota

## Dlaczego quota governance jest krytyczny
YouTube Data API ma dzienne limity jednostek. Bez monitoringu łatwo zablokować pipeline publikacji.

## Podejście w StudioFlow
- Każde wywołanie API logowane jest do `YouTubeQuotaLedgerEntry`.
- Zapis obejmuje: organization/workspace/channel/project/run, metodę, koszt, success/failure, retry.
- `YouTubeClientQuotaWrapper` loguje zarówno sukcesy, jak i wyjątki.

## Domyślne koszty metod
- `videos.insert`: 1600
- `videos.update`: 50
- `videos.list`: 1
- `search.list`: 100
- `captions.insert`: 400
- `thumbnails.set`: 50
- fallback dla nieznanych metod: 1

## Jak interpretować quota
- Quota w ledgerze to koszt operacyjny i sygnał do optymalizacji workflow.
- Retry podnosi całkowite zużycie, dlatego ma osobne pole `retry_of_id`.
