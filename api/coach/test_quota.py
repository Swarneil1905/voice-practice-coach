import os
import tempfile
from concurrent.futures import ThreadPoolExecutor
from unittest import TestCase
from unittest.mock import patch
from .quota import reserve


class QuotaTests(TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {"QUOTA_DATABASE": self.directory.name + "/quota.sqlite", "AI_DAILY_LIMIT": "3", "AI_MONTHLY_LIMIT": "4"})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.directory.cleanup()

    def test_allowance_survives_new_connections_and_daily_reset(self):
        now = 1792886400
        self.assertTrue(all(reserve("ai", now) for _ in range(3)))
        self.assertFalse(reserve("ai", now))
        self.assertTrue(reserve("ai", now + 86400))
        self.assertFalse(reserve("ai", now + 86400))

    def test_concurrent_reservations_do_not_exceed_limit(self):
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda _: reserve("ai", 1792886400), range(12)))
        self.assertEqual(sum(results), 3)

    def test_voice_lease_expires(self):
        self.assertTrue(reserve("voice", 1792886400))
        self.assertTrue(reserve("voice", 1792886400))
        self.assertFalse(reserve("voice", 1792886400))
        self.assertTrue(reserve("voice", 1792887001))
        self.assertFalse(reserve("voice", 1792888000))

    def test_production_fails_closed_without_storage(self):
        with patch.dict(os.environ, {"QUOTA_DATABASE": "", "DJANGO_DEBUG": "false"}):
            self.assertFalse(reserve("ai"))
