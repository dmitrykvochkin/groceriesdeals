"""Anonymous identity helpers derived from ChatGPT request metadata."""

from __future__ import annotations

import hashlib
import hmac
from collections.abc import Mapping
from typing import Any

_SUBJECT_META_KEY = "openai/subject"


def extract_openai_subject(meta: Any) -> str | None:
    """Return a non-empty openai/subject from request meta, or None."""
    if meta is None:
        return None

    value: Any = None
    if isinstance(meta, Mapping):
        value = meta.get(_SUBJECT_META_KEY)
    else:
        dumped = getattr(meta, "model_dump", None)
        if callable(dumped):
            value = dumped().get(_SUBJECT_META_KEY)
        else:
            value = getattr(meta, _SUBJECT_META_KEY, None)

    if not isinstance(value, str):
        return None
    subject = value.strip()
    return subject or None


def derive_anonymous_key(secret: str, subject: str) -> str:
    """Return hex HMAC-SHA256(secret, 'openai:' + subject)."""
    return hmac.new(
        secret.encode("utf-8"),
        f"openai:{subject}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
