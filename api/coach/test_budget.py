import io
import json
import os
import sqlite3
import tempfile
import wave
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from .budget import reserve_cost


class BudgetTests(TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = self.temp.name + "/budget.sqlite"
        sqlite3.connect(self.path).close()
        self.env = patch.dict(os.environ, {"QUOTA_DATABASE": self.path, "VOICE_GATEWAY_SECRET": "test-worker-secret", "OPENAI_API_KEY": "test-key"})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def test_atomic_shared_lifetime_ceiling(self):
        with ThreadPoolExecutor(max_workers=12) as pool:
            results = list(pool.map(lambda _: reserve_cost("chat"), range(60)))
        self.assertEqual(sum(results), 36)
        self.assertFalse(reserve_cost("speech"))
        self.assertFalse(reserve_cost("transcription"))
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute("SELECT reserved FROM lifetime_budget").fetchone()[0], 2_000_000)
        self.assertFalse(reserve_cost("chat"))

    def test_missing_storage_fails_closed(self):
        with patch.dict(os.environ, {"QUOTA_DATABASE": self.path + ".missing"}):
            self.assertFalse(reserve_cost("chat"))

    @patch("coach.provider.httpx.Client")
    def test_gateway_denies_unauthenticated_requests_before_spend(self, upstream):
        response = Client(enforce_csrf_checks=True).post("/api/provider/audio/speech", data='{"input":"Hello"}', content_type="application/json")
        self.assertEqual(response.status_code, 403)
        upstream.assert_not_called()

    @patch("coach.provider.reserve_cost", return_value=False)
    @patch("coach.provider.httpx.Client")
    def test_exhausted_budget_never_calls_provider(self, upstream, reserve):
        response = self.client.post("/api/provider/chat/completions", data=json.dumps({"messages":[{"role":"user","content":"Hello"}]}), content_type="application/json", HTTP_X_VOICE_WORKER_KEY="test-worker-secret")
        self.assertEqual(response.status_code, 429)
        upstream.assert_not_called()

    @patch("coach.provider.httpx.Client")
    def test_overlong_audio_never_reaches_provider(self, upstream):
        audio = io.BytesIO()
        with wave.open(audio, "wb") as wav:
            wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(8000)
            wav.writeframes(bytes(8000 * 2 * 61))
        response = self.client.post("/api/provider/audio/transcriptions", {"file": SimpleUploadedFile("test.wav", audio.getvalue(), content_type="audio/wav")}, HTTP_X_VOICE_WORKER_KEY="test-worker-secret")
        self.assertEqual(response.status_code, 400)
        upstream.assert_not_called()

    @patch("coach.provider.httpx.Client")
    def test_model_and_token_limits_override_worker_input(self, factory):
        upstream = factory.return_value
        upstream.send.return_value.headers = {"content-type":"text/event-stream"}
        upstream.send.return_value.iter_bytes.return_value = iter([b"data: [DONE]\n\n"])
        response = self.client.post("/api/provider/chat/completions", data=json.dumps({"model":"expensive-model","max_tokens":999999,"messages":[{"role":"user","content":"Hello"}]}), content_type="application/json", HTTP_X_VOICE_WORKER_KEY="test-worker-secret")
        self.assertEqual(response.status_code, 200)
        body = upstream.build_request.call_args.kwargs["json"]
        self.assertEqual(body["model"], "gpt-4.1-mini")
        self.assertEqual(body["max_tokens"], 600)
        self.assertEqual(b"".join(response.streaming_content), b"data: [DONE]\n\n")
        upstream.close.assert_called_once()

    @patch("coach.provider.httpx.Client")
    def test_oversized_speech_and_nontext_inputs_are_rejected(self, upstream):
        for path, data in [("audio/speech", {"input":"x"*4001}), ("chat/completions", {"messages":[{"role":"user","content":[{"type":"image_url"}]}]})]:
            response = self.client.post("/api/provider/"+path, data=json.dumps(data), content_type="application/json", HTTP_X_VOICE_WORKER_KEY="test-worker-secret")
            self.assertEqual(response.status_code, 400)
        upstream.assert_not_called()
