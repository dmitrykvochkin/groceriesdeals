"""Tests for anonymous identity helpers."""

from __future__ import annotations

import hashlib
import hmac
import unittest
from unittest.mock import MagicMock

from mcp.types import RequestParams
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from groceriesdeals.db.models import User
from groceriesdeals.db.session import engine
from groceriesdeals.identity import (
    derive_anonymous_key,
    ensure_user,
    extract_openai_subject,
)


class DeriveAnonymousKeyTests(unittest.TestCase):
    def test_matches_hmac_sha256_hex_with_openai_prefix(self) -> None:
        secret = "test-secret"
        subject = "v1/opaque-user-value"
        expected = hmac.new(
            secret.encode("utf-8"),
            f"openai:{subject}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        self.assertEqual(derive_anonymous_key(secret, subject), expected)

    def test_same_inputs_are_stable(self) -> None:
        first = derive_anonymous_key("secret", "subject-a")
        second = derive_anonymous_key("secret", "subject-a")
        self.assertEqual(first, second)

    def test_different_subjects_differ(self) -> None:
        a = derive_anonymous_key("secret", "subject-a")
        b = derive_anonymous_key("secret", "subject-b")
        self.assertNotEqual(a, b)


class ExtractOpenaiSubjectTests(unittest.TestCase):
    def test_from_mapping(self) -> None:
        self.assertEqual(
            extract_openai_subject({"openai/subject": "v1/user"}),
            "v1/user",
        )

    def test_from_request_params_meta(self) -> None:
        meta = RequestParams.Meta.model_validate({"openai/subject": "v1/user"})
        self.assertEqual(extract_openai_subject(meta), "v1/user")

    def test_missing_returns_none(self) -> None:
        self.assertIsNone(extract_openai_subject({}))
        self.assertIsNone(extract_openai_subject(None))

    def test_blank_returns_none(self) -> None:
        self.assertIsNone(extract_openai_subject({"openai/subject": "  "}))
        self.assertIsNone(extract_openai_subject({"openai/subject": ""}))


class EnsureUserTests(unittest.TestCase):
    def test_creates_then_reuses_user(self) -> None:
        key = derive_anonymous_key("ensure-user-test-secret", "ensure-user-subject")
        with Session(engine) as session:
            existing = session.exec(
                select(User).where(User.anonymous_key == key)
            ).first()
            if existing is not None:
                session.delete(existing)
                session.commit()

        with Session(engine) as session:
            created = ensure_user(session, key)
            session.commit()
            created_id = created.id

        with Session(engine) as session:
            reused = ensure_user(session, key)
            session.commit()
            self.assertEqual(reused.id, created_id)
            count = len(
                session.exec(select(User).where(User.anonymous_key == key)).all()
            )
            self.assertEqual(count, 1)

    def test_integrity_error_reselects_existing(self) -> None:
        key = "collision-key-for-ensure-user"
        with Session(engine) as session:
            existing = session.exec(
                select(User).where(User.anonymous_key == key)
            ).first()
            if existing is None:
                session.add(User(anonymous_key=key))
                session.commit()
                existing = session.exec(
                    select(User).where(User.anonymous_key == key)
                ).one()
            existing_id = existing.id

        session = MagicMock(spec=Session)
        session.exec.return_value.first.side_effect = [
            None,
            User(id=existing_id, anonymous_key=key),
        ]
        session.commit.side_effect = IntegrityError(
            "duplicate",
            params=None,
            orig=Exception("unique"),
        )
        session.rollback.return_value = None

        user = ensure_user(session, key)
        self.assertEqual(user.id, existing_id)
        session.rollback.assert_called_once()


if __name__ == "__main__":
    unittest.main()
