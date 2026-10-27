"""Concrete rehearsal tasks derived from a transparent topic checklist."""

from .rubric import baseline_review

EXERCISES = {
    "cache": [
        (
            "Choose a freshness budget",
            "State an acceptable stale-data window, choose a TTL, and explain what makes that TTL unsafe.",
            "For a noncritical description I would allow 60 seconds of staleness; checkout must recheck authoritative stock.",
        ),
        (
            "Trace an inventory update",
            "Walk through a stock change from the database to every cached reader. Include one lost invalidation event.",
            "Commit the stock change, publish a versioned event, and reject an older version when consumers replay events.",
        ),
        (
            "Design the fallback",
            "Explain the timeout, fallback and overload limit when the cache is unavailable.",
            "Use a short cache timeout and a bounded database fallback; shed load when the database limit is reached.",
        ),
    ],
    "queue": [
        (
            "Show the atomic boundary",
            "Describe where the deduplication key is stored and which writes commit together.",
            "Insert the event key and create the order in one database transaction with a unique constraint.",
        ),
        (
            "Bound the retry loop",
            "Choose retryable failures, a backoff policy, an attempt limit and an owner for exhausted retries.",
            "Retry transient timeouts with exponential backoff and jitter; move exhausted jobs to a dead letter queue.",
        ),
        (
            "Rehearse a crash",
            "Trace a crash after commit but before acknowledgement. Explain safe replay and how failed work is discovered.",
            "The replay finds the committed idempotency key, skips the duplicate write and acknowledges the message.",
        ),
    ],
    "scale": [
        (
            "Choose a diagnostic",
            "Name a metric, where you measure it, and what result would change your scaling decision.",
            "Compare p95 latency, database wait time and CPU saturation before adding application replicas.",
        ),
        (
            "Explain request routing",
            "Describe how load reaches healthy replicas and how sessions survive a replica failure.",
            "Route through a health checked load balancer and keep session state outside application replicas.",
        ),
        (
            "Define a rollback gate",
            "Choose a representative load test, a failure test and a rollback threshold.",
            "Increase load gradually, remove one replica, and roll back if p95 latency exceeds the agreed threshold.",
        ),
    ],
}


def build_plan(scenario, answer, previous=None):
    review = baseline_review(scenario, answer)
    tasks = []
    for i, row in enumerate(review["coverage"]):
        title, exercise, example = EXERCISES[scenario][i]
        tasks.append(
            {
                "topic": row["title"],
                "title": title,
                "exercise": exercise,
                "example": example,
                "priority": "deepen" if row["covered"] else "address_gap",
            }
        )
    tasks.sort(key=lambda x: x["priority"] != "address_gap")
    comparison = None
    if previous is not None:
        before = baseline_review(scenario, previous)
        old = {x["title"] for x in before["coverage"] if x["covered"]}
        new = {x["title"] for x in review["coverage"] if x["covered"]}
        comparison = {
            "before_topics": len(old),
            "after_topics": len(new),
            "new_topics": sorted(new - old),
            "lost_topics": sorted(old - new),
            "word_change": review["word_count"] - before["word_count"],
            "answer_changed": answer.strip() != previous.strip(),
            "meaning": "Changes in mentioned topics, not proof of technical correctness or interview readiness.",
        }
    return {
        "practice_plan": tasks,
        "comparison": comparison,
        "speaking_estimate": {
            "min_seconds": round(review["word_count"] / 160 * 60),
            "max_seconds": round(review["word_count"] / 120 * 60),
            "basis": "Text length at 120 to 160 words per minute, not measured speech.",
        },
    }
