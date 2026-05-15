from dataclasses import dataclass


@dataclass(frozen=True)
class GateReason:
    code: str
    field: str
    actual: float
    threshold: float
    op: str

    def as_dict(self) -> dict:
        return {
            "code": self.code,
            "field": self.field,
            "actual": round(float(self.actual), 3),
            "threshold": round(float(self.threshold), 3),
            "op": self.op,
        }


class AngleValidationService:
    """Deterministic approval gate evaluator for persisted angle scores."""

    THRESHOLDS: dict[str, tuple[str, float, str]] = {
        "hook_clarity": ("HOOK_CLARITY_TOO_LOW", 0.35, "gte"),
        "risk": ("RISK_TOO_HIGH", 0.15, "lte"),
        "overall_score": ("OVERALL_SCORE_TOO_LOW", 0.6, "gte"),
    }

    def evaluate(self, score_payload: dict | None) -> dict:
        payload = score_payload or {}
        reasons: list[dict] = []
        for field, (code, threshold, op) in self.THRESHOLDS.items():
            raw = payload.get(field)
            actual = self._to_float(raw)
            if actual is None:
                reasons.append(
                    GateReason(
                        code="MISSING_REQUIRED_SCORE",
                        field=field,
                        actual=float("nan"),
                        threshold=threshold,
                        op="present",
                    ).as_dict()
                )
                continue
            if op == "gte" and actual < threshold:
                reasons.append(GateReason(code=code, field=field, actual=actual, threshold=threshold, op=op).as_dict())
            if op == "lte" and actual > threshold:
                reasons.append(GateReason(code=code, field=field, actual=actual, threshold=threshold, op=op).as_dict())

        passed = len(reasons) == 0
        return {"gate_passed": passed, "rejection_reasons": reasons}

    @staticmethod
    def _to_float(value) -> float | None:
        try:
            if value is None:
                return None
            return float(value)
        except (TypeError, ValueError):
            return None
