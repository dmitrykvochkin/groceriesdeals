"""Anonymous identity helpers derived from ChatGPT request metadata."""

from __future__ import annotations

import hashlib
import hmac
from collections.abc import Mapping
from typing import Any

from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from groceriesdeals.db.models import User

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


def ensure_user(session: Session, anonymous_key: str) -> User:
    """Return an existing User for anonymous_key, creating one if needed."""
    existing = session.exec(
        select(User).where(User.anonymous_key == anonymous_key)
    ).first()
    if existing is not None:
        return existing

    user = User(anonymous_key=anonymous_key)
    session.add(user)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        existing = session.exec(
            select(User).where(User.anonymous_key == anonymous_key)
        ).first()
        if existing is None:
            raise
        return existing

    session.refresh(user)
    return user


def record_tool_request(session: Session, anonymous_key: str) -> None:
    """Ensure the user exists and atomically increment their tool request count."""
    user = ensure_user(session, anonymous_key)
    session.exec(
        update(User)
        .where(User.id == user.id)
        .values(tool_request_count=User.tool_request_count + 1)
    )