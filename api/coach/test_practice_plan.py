from django.test import TestCase
from .practice_plan import build_plan
from .rubric import SCENARIOS


class PracticePlanTests(TestCase):
    def test_missing_topic_has_a_specific_exercise(self):
        plan = build_plan(
            "queue", "I would write orders in a transaction with a unique key."
        )
        self.assertEqual(plan["practice_plan"][0]["title"], "Bound the retry loop")
        self.assertEqual(plan["practice_plan"][0]["priority"], "address_gap")

    def test_comparison_reports_losses_as_well_as_gains(self):
        plan = build_plan(
            "queue",
            "I would retry with backoff and inspect the dead letter queue.",
            "I would use a unique transaction key to avoid duplicates.",
        )
        self.assertEqual(plan["comparison"]["lost_topics"], ["Idempotency"])
        self.assertIn("Retry strategy", plan["comparison"]["new_topics"])
        self.assertEqual(plan["comparison"]["before_topics"], 1)

    def test_same_answer_is_not_presented_as_improvement(self):
        answer = "I would use a short TTL and a database fallback."
        comparison = build_plan("cache", answer, answer)["comparison"]
        self.assertFalse(comparison["answer_changed"])
        self.assertEqual(comparison["new_topics"], [])

    def test_all_scenarios_supply_complete_drills(self):
        for scenario in SCENARIOS:
            plan = build_plan(scenario, "I will begin by discussing the requirements.")
            self.assertEqual(len(plan["practice_plan"]), 3)
            self.assertTrue(
                all(x["exercise"] and x["example"] for x in plan["practice_plan"])
            )
