# Compliance Engine

## Zakres kontroli
Compliance ocenia ryzyka:
- AI disclosure
- inauthentic content
- repetitive content
- copyright
- sensitive claims
- clickbait
- asset license
- synthetic media realism

## Mechanika scoringu i poziomów ryzyka
- Wejście zawiera `score` (0-100) i metadane ryzyk.
- Normalizacja:
  - `<=39` => `high`
  - `40-69` => `medium`
  - `>=70` => `low`
- Jeśli wystąpią warunki blokujące, poziom ustawiany jest na `blocked`.

## Blocking issues
Publikacja/approval są blokowane m.in. gdy:
- `copyright_risk == high`
- `asset_license_risk == high`
- `repetitive_content_risk == high`
- wymagany disclosure AI nie ma decyzji użytkownika

## Repetitive content
Silnik porównuje bieżący projekt do poprzednich i dodaje:
- poziom ryzyka podobieństwa,
- powody (`reasons`),
- rekomendacje (`recommendations`).

## Policy note
Compliance to mechanizm redukcji ryzyka operacyjnego, **nie** porada prawna.
