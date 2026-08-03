import json
from unittest.mock import patch
from django.test import TestCase, Client
from django.core.cache import cache


class ReviewTests(TestCase):
    def setUp(self):
        cache.clear()

    def post(self, data):
        return self.client.post(
            "/api/practice/review",
            data=json.dumps(data),
            content_type="application/json",
        )

    def test_baseline_cites_actual_answer(self):
        answer = "I would use a short TTL. Inventory events invalidate cached records. A timeout falls back to the database."
        r = self.post({"scenario": "cache", "answer": answer})
        self.assertEqual(r.status_code, 200)
        for row in r.json()["coverage"]:
            self.assertTrue(row["covered"])
            self.assertIn(row["evidence"], answer)

    def test_missing_topics_are_not_fabricated(self):
        r = self.post(
            {
                "scenario": "cache",
                "answer": "I will first talk to the team to understand the product.",
            }
        )
        self.assertFalse(any(x["covered"] for x in r.json()["coverage"]))

    def test_invalid_scenario_and_input(self):
        self.assertEqual(
            self.post({"scenario": "unknown", "answer": "x" * 30}).status_code, 400
        )
        self.assertEqual(
            self.post({"scenario": "cache", "answer": "x" * 8001}).status_code, 400
        )
        self.assertEqual(self.post([]).status_code, 400)

    def test_ai_requires_explicit_consent(self):
        self.assertEqual(
            self.post(
                {"scenario": "cache", "answer": "x" * 30, "mode": "ai"}
            ).status_code,
            400,
        )

    def test_csrf_is_enforced(self):
        c = Client(enforce_csrf_checks=True)
        self.assertEqual(
            c.post(
                "/api/practice/review", data="{}", content_type="application/json"
            ).status_code,
            403,
        )
        c.get("/api/capabilities")
        self.assertIn("csrftoken", c.cookies)

    @patch.dict("os.environ", {"ENABLE_VOICE": "false"})
    def test_voice_is_closed_without_configuration(self):
        self.assertEqual(
            self.client.post(
                "/api/voice/token", data="{}", content_type="application/json"
            ).status_code,
            503,
        )

    def test_rate_limit(self):
        for _ in range(30):
            self.post({"scenario": "cache", "answer": "x" * 30})
        self.assertEqual(
            self.post({"scenario": "cache", "answer": "x" * 30}).status_code, 429
        )

    def test_non_string_scenario_returns_400(self):
        self.assertEqual(
            self.post({"scenario": [], "answer": "x" * 30}).status_code, 400
        )

    @patch.dict(
        "os.environ",
        {
            "ENABLE_VOICE": "true",
            "LIVEKIT_URL": "wss://example.invalid",
            "LIVEKIT_API_KEY": "local-test-key",
            "LIVEKIT_API_SECRET": "test-secret-which-is-at-least-32-bytes-long",
        },
    )
    def test_token_scope_and_expiry(self):
        import jwt

        r = self.client.post(
            "/api/voice/token",
            data=json.dumps({"scenario": "cache", "consent": True}),
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 200)
        token = jwt.decode(
            r.json()["token"],
            "test-secret-which-is-at-least-32-bytes-long",
            algorithms=["HS256"],
        )
        self.assertLessEqual(token["exp"] - token["nbf"], 120)
        self.assertEqual(token["video"]["canPublishSources"], ["microphone"])
        self.assertFalse(token["video"]["canPublishData"])
        self.assertEqual(
            token["roomConfig"]["agents"][0]["agentName"], "practice-coach"
        )

    @patch.dict("os.environ", {"AI_API_KEY": "local-test-only"})
    @patch("coach.views.httpx.Client")
    def test_invalid_ai_shape_returns_controlled_error(self, client):
        response = client.return_value.__enter__.return_value.post.return_value
        response.json.return_value = {"choices": [{"message": {"content": "{}"}}]}
        self.assertEqual(
            self.post(
                {"scenario": "cache", "answer": "x" * 30, "mode": "ai", "consent": True}
            ).status_code,
            502,
        )
