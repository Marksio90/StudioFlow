from app.services.repetitive_content_detector import ProjectContent, RepetitiveContentDetector


def test_high_risk_for_similar_title_hook_structure():
    detector = RepetitiveContentDetector()
    current = ProjectContent(
        project_id="new",
        title="Jak zbudować agenta AI w 10 minut",
        hook="Ten sam framework da Ci 2x produktywność",
        outline=["Intro", "Setup", "Demo", "CTA"],
        script="A\nB\nC\nD",
        description="Przewodnik krok po kroku",
        thumbnail_brief="duży napis 10 minut",
        cta="Subskrybuj",
        topic="agent ai",
        angle="tutorial",
    )
    prev = [current.model_copy(update={"project_id": "old-1"})]
    result = detector.detect(current, prev)
    assert result.risk_level == "high"
    assert result.overall_similarity >= 0.8


def test_medium_or_low_for_same_topic_but_different_angle_structure():
    detector = RepetitiveContentDetector()
    current = ProjectContent(
        project_id="new",
        title="Agent AI: błędy produkcyjne",
        hook="Najczęstsze awarie na produkcji",
        outline=["Problem", "Incident", "Fixes"],
        script="S1\nS2",
        description="Analiza awarii",
        thumbnail_brief="alert produkcja",
        cta="Napisz swoje doświadczenia",
        topic="agent ai",
        angle="postmortem",
    )
    old = ProjectContent(
        project_id="old-2",
        title="Agent AI od zera",
        hook="Zobacz szybki tutorial",
        outline=["Intro", "Setup", "Demo", "CTA"],
        script="A\nB\nC\nD\nE",
        description="Instrukcja wdrożenia",
        thumbnail_brief="kod i strzałki",
        cta="Subskrybuj",
        topic="agent ai",
        angle="tutorial",
    )
    result = detector.detect(current, [old])
    assert result.overall_similarity < 0.8
    assert result.risk_level in {"low", "medium"}
