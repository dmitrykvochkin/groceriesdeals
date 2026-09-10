"""Tests for anonymous identity helpers."""

from __future__ import annotations

import hashlib
import hmac
import unittest

from mcp.types import RequestParams
from groceriesdeals.identity import (
    derive_anonymous_key,
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

if __name__ == "__main__":
    unittest.main()
