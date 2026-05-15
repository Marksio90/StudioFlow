from __future__ import annotations

import json
import re
from typing import Any

_REDACTED = "[REDACTED]"
_SECRET_KEY_PATTERN = re.compile(r"(?i)(api[_-]?key|authorization|token|bearer|secret|password)")
_BEARER_VALUE_PATTERN = re.compile(r"(?i)\bbearer\s+[a-z0-9._\-+/=]+")
_KEY_VALUE_PATTERN = re.compile(r'(?i)\b(api[_-]?key|authorization|token|secret|password)\b\s*[:=]\s*["\']?([^,\s\}\]\"\']+)')


def redact_secrets(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: (_REDACTED if _SECRET_KEY_PATTERN.search(str(k)) else redact_secrets(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [redact_secrets(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_secrets(item) for item in value)
    if isinstance(value, str):
        text = _BEARER_VALUE_PATTERN.sub(f"Bearer {_REDACTED}", value)
        text = _KEY_VALUE_PATTERN.sub(lambda m: f"{m.group(1)}={_REDACTED}", text)
        return text
    return value


def redacted_text(value: Any) -> str:
    redacted = redact_secrets(value)
    if isinstance(redacted, str):
        return redacted
    return json.dumps(redacted, default=str, sort_keys=True)
