from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Protocol

from pydantic import BaseModel, Field

SIMILARITY_WEIGHTS = {
    "lexical": 0.30,
    "semantic": 0.30,
    "structural": 0.20,
    "metadata": 0.20,
}


class EmbeddingsProvider(Protocol):
    def embed(self, text: str) -> list[float]: ...


class MockEmbeddingsProvider:
    def embed(self, text: str) -> list[float]:
        tokens = _tokenize(text)
        v = [0.0] * 8
        for i, token in enumerate(tokens):
            v[i % len(v)] += (sum(ord(ch) for ch in token) % 97) / 100.0
        return v


class ProjectContent(BaseModel):
    project_id: str
    title: str = ""
    hook: str = ""
    outline: list[str] = Field(default_factory=list)
    script: str = ""
    description: str = ""
    thumbnail_brief: str = ""
    cta: str = ""
    topic: str = ""
    angle: str = ""


class SimilarProject(BaseModel):
    project_id: str
    similarity: float


class RepetitiveContentResult(BaseModel):
    overall_similarity: float
    risk_level: str
    most_similar_projects: list[SimilarProject]
    reasons: list[str]
    recommendations: list[str]


@dataclass
class ScoredProject:
    project_id: str
    score: float


class RepetitiveContentDetector:
    def __init__(self, embeddings_provider: EmbeddingsProvider | None = None) -> None:
        self.embeddings_provider = embeddings_provider or MockEmbeddingsProvider()

    def detect(self, current: ProjectContent, previous_projects: list[ProjectContent]) -> RepetitiveContentResult:
        if not previous_projects:
            return RepetitiveContentResult(
                overall_similarity=0.0,
                risk_level="low",
                most_similar_projects=[],
                reasons=["Brak wcześniejszych projektów do porównania."],
                recommendations=["Buduj bazę referencyjną historii publikacji."],
            )

        scored: list[ScoredProject] = []
        reason_bits: list[str] = []
        for prev in previous_projects:
            components = self._similarity_components(current, prev)
            penalties = self._heuristic_penalty(current, prev)
            total = max(0.0, min(1.0, self._weighted_similarity(components) + penalties))
            scored.append(ScoredProject(project_id=prev.project_id, score=total))
            reason_bits.extend(self._build_reasons(prev.project_id, components))

        scored.sort(key=lambda x: x.score, reverse=True)
        top = scored[:3]
        overall = top[0].score
        level = self._risk_level(overall)
        reasons = reason_bits[:4] or ["Podobieństwo wyliczone hybrydowo (lexical/semantic/structural/metadata)."]
        recommendations = self._recommendations(level)
        return RepetitiveContentResult(
            overall_similarity=round(overall, 4),
            risk_level=level,
            most_similar_projects=[SimilarProject(project_id=s.project_id, similarity=round(s.score, 4)) for s in top],
            reasons=reasons,
            recommendations=recommendations,
        )

    def _similarity_components(self, a: ProjectContent, b: ProjectContent) -> dict[str, float]:
        return {
            "lexical": self._lexical_similarity(a, b),
            "semantic": self._semantic_similarity(a, b),
            "structural": self._structural_similarity(a, b),
            "metadata": self._metadata_similarity(a, b),
        }

    def _weighted_similarity(self, components: dict[str, float]) -> float:
        return sum(SIMILARITY_WEIGHTS[key] * components[key] for key in SIMILARITY_WEIGHTS)

    def _build_reasons(self, project_id: str, components: dict[str, float]) -> list[str]:
        reasons: list[str] = []
        if components["lexical"] > 0.8:
            reasons.append(f"Wysoka zgodność leksykalna z {project_id}")
        if components["structural"] > 0.8:
            reasons.append(f"Wysoka zgodność struktury z {project_id}")
        return reasons

    def _risk_level(self, score: float) -> str:
        if score >= 0.8:
            return "high"
        if score >= 0.6:
            return "medium"
        return "low"

    def _lexical_similarity(self, a: ProjectContent, b: ProjectContent) -> float:
        fields = [a.title + " " + a.hook + " " + a.description + " " + a.cta, b.title + " " + b.hook + " " + b.description + " " + b.cta]
        return _jaccard(_tokenize(fields[0]), _tokenize(fields[1]))

    def _semantic_similarity(self, a: ProjectContent, b: ProjectContent) -> float:
        text_a = " ".join([a.title, a.hook, a.script, a.topic, a.angle])
        text_b = " ".join([b.title, b.hook, b.script, b.topic, b.angle])
        return _cosine(self.embeddings_provider.embed(text_a), self.embeddings_provider.embed(text_b))

    def _structural_similarity(self, a: ProjectContent, b: ProjectContent) -> float:
        outline_sim = _jaccard([x.lower() for x in a.outline], [x.lower() for x in b.outline])
        a_sections = len(re.findall(r"\n", a.script)) + 1
        b_sections = len(re.findall(r"\n", b.script)) + 1
        section_sim = 1.0 - min(abs(a_sections - b_sections), 10) / 10
        return max(0.0, min(1.0, 0.6 * outline_sim + 0.4 * section_sim))

    def _metadata_similarity(self, a: ProjectContent, b: ProjectContent) -> float:
        topic_sim = _jaccard(_tokenize(a.topic), _tokenize(b.topic))
        thumb_sim = _jaccard(_tokenize(a.thumbnail_brief), _tokenize(b.thumbnail_brief))
        return 0.7 * topic_sim + 0.3 * thumb_sim

    def _heuristic_penalty(self, a: ProjectContent, b: ProjectContent) -> float:
        penalty = 0.0
        if _equal_non_empty(a.title, b.title):
            penalty += 0.1
        if _equal_non_empty(a.hook, b.hook):
            penalty += 0.1
        if a.angle and b.angle and a.angle.lower() != b.angle.lower():
            penalty -= 0.1
        return penalty

    def _recommendations(self, level: str) -> list[str]:
        if level == "high":
            return ["Zmień hook i strukturę skryptu.", "Zastosuj nowy angle i inny CTA."]
        if level == "medium":
            return ["Doprecyzuj unikalny angle i przeorganizuj outline."]
        return ["Podobieństwo akceptowalne; monitoruj dalszą dywersyfikację."]


def _equal_non_empty(a: str, b: str) -> bool:
    a_norm = a.strip().lower()
    b_norm = b.strip().lower()
    return bool(a_norm and b_norm and a_norm == b_norm)


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[\w]+", text.lower())


def _jaccard(a: list[str], b: list[str]) -> float:
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def _cosine(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return max(0.0, min(1.0, dot / (na * nb)))
