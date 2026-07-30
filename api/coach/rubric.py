import re

SCENARIOS = {
    "cache": {
        "title": "When a cache becomes a problem",
        "prompt": "Design a fast catalog with frequently changing inventory. Explain caching, invalidation, and safe checkout.",
        "criteria": [
            (
                "Freshness and TTL",
                ["ttl", "time to live", "expir", "freshness", "stale"],
                "How would you choose the cache lifetime?",
            ),
            (
                "Invalidation and consistency",
                ["invalidat", "version", "event", "consisten", "checkout", "inventory"],
                "What happens when inventory changes while a recommendation is cached?",
            ),
            (
                "Failure and recovery",
                ["fallback", "fail", "timeout", "retry", "circuit", "recover"],
                "How does the system respond when the cache is unavailable?",
            ),
        ],
    },
    "queue": {
        "title": "A queue that never loses an order",
        "prompt": "A payment webhook may arrive twice and a worker may crash after creating an order. Design duplicate prevention and recovery.",
        "criteria": [
            (
                "Idempotency",
                ["idempoten", "unique", "dedup", "duplicate", "transaction"],
                "Where would you enforce uniqueness?",
            ),
            (
                "Retry strategy",
                ["backoff", "retry", "retries", "attempt", "delay"],
                "How do retries avoid making an outage worse?",
            ),
            (
                "Failure and recovery",
                ["dead letter", "dead-letter", "fail", "recover", "atomic", "outbox"],
                "How do you find and replay a permanently failed job?",
            ),
        ],
    },
    "scale": {
        "title": "The morning your traffic doubles",
        "prompt": "Response time rises as traffic doubles. Identify the bottleneck, distribute load, and verify your fix.",
        "criteria": [
            (
                "Measurement",
                [
                    "latency",
                    "metric",
                    "trace",
                    "percentile",
                    "p95",
                    "profil",
                    "bottleneck",
                ],
                "What would you measure before scaling?",
            ),
            (
                "Load distribution",
                ["load balanc", "replica", "horizontal", "distribut", "stateless"],
                "How would you distribute requests safely?",
            ),
            (
                "Failure and recovery",
                ["health", "fail", "test", "rollback", "recover", "timeout"],
                "How would you test the failure path?",
            ),
        ],
    },
}


def baseline_review(scenario, answer):
    spec = SCENARIOS[scenario]
    sentences = re.split(r"(?<=[.!?])\s+|\n+", answer.strip())
    coverage = []
    for title, keywords, question in spec["criteria"]:
        evidence = next(
            (s for s in sentences if any(k in s.lower() for k in keywords)), None
        )
        coverage.append(
            {
                "title": title,
                "covered": bool(evidence),
                "evidence": evidence[:400] if evidence else question,
            }
        )
    missing = next(
        (
            criterion[2]
            for criterion, result in zip(spec["criteria"], coverage)
            if not result["covered"]
        ),
        None,
    )
    return {
        "coverage": coverage,
        "next_question": missing
        or "Which assumption would you test first, and what result would change your design?",
        "disclaimer": "This baseline detects topic mentions. It does not judge correctness or assign a technical ability score.",
        "word_count": len(answer.split()),
        "mode": "keyword_baseline",
    }
