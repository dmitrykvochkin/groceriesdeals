"""Unit tests for PostHog identity and activity-session primitives."""

from __future__ import annotations

import unittest
import uuid
from datetime import datetime, timedelta, timezone

from groceriesdeals.mcp_posthog import SessionTrackingState, uuid7


class UUID7Tests(unittest.TestCase):
    def test_version_variant_and_timestamp(self) -> None:
        timestamp = datetime(2026, 8, 18, 12, 34, 56, 789000, tzinfo=timezone.utc)
        generated = uuid.UUID(uuid7(timestamp))

        self.assertEqual(generated.version, 7)
        self.assertEqual(generated.variant, uuid.RFC_4122)
        self.assertEqual(generated.int >> 80, int(timestamp.timestamp() * 1000))


class SessionTrackingStateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.started = datetime(2026, 8, 18, 12, 0, tzinfo=timezone.utc)

    def test_reuses_session_within_activity_window(self) -> None:
        state = SessionTrackingState.create(self.started)
        original = state.posthog_session_id
        state.touch(self.started + timedelta(minutes=29, seconds=59))
        self.assertEqual(state.posthog_session_id, original)

    def test_rotates_after_thirty_minutes_idle(self) -> None:
        state = SessionTrackingState.create(self.started)
        original = state.posthog_session_id
        state.touch(self.started + timedelta(minutes=30))
        self.assertNotEqual(state.posthog_session_id, original)

    def test_rotates_after_twenty_four_hours_total(self) -> None:
        state = SessionTrackingState.create(self.started)
        original = state.posthog_session_id
        state.last_activity_at = self.started + timedelta(hours=23, minutes=59)
        state.touch(self.started + timedelta(hours=24))
        self.assertNotEqual(state.posthog_session_id, original)


if __name__ == "__main__":
    unittest.main()
