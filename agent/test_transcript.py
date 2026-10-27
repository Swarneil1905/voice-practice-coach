import json
import unittest
from transcript import append_transcript


class TranscriptTests(unittest.TestCase):
    def test_appends_final_turns(self):
        text, packet = append_transcript("First answer.", " More detail. ")
        self.assertEqual(text, "First answer. More detail.")
        self.assertEqual(json.loads(packet)["text"], text)

    def test_escaped_and_multibyte_text_stays_within_packet_limit(self):
        for value in ["\\" * 20000, "\U0001f600" * 20000, "\n" * 20000, "a" * 20000]:
            text, packet = append_transcript("", value)
            self.assertLessEqual(len(packet), 12000)
            self.assertLessEqual(len(text), 8000)
            self.assertEqual(json.loads(packet)["text"], text)
