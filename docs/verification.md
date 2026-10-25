# Verification record

Verified on 2026-10-25 against the public Railway deployment.

| Check | Result |
| --- | --- |
| Django tests | 21 passed, including concurrent lifetime budget limits, authentication and provider bounds |
| Voice session deadline tests | 3 passed |
| GitHub Actions | API, frontend, Compose, production container, voice worker build and publish passed |
| Public HTTPS gateway | Health, security headers, stylesheet delivery and CSRF checks passed |
| Text review | Baseline evidence and a real funded AI feedback request passed |
| LiveKit | Worker registered; scoped room token connected successfully |
| Voice provider gateway | Real chat, speech synthesis and speech transcription requests succeeded through the shared budget gateway |
| Synthetic voice exchange | Received coach greeting, published local synthetic speech, and received at least 25 non-silent response audio frames |
| Rate limit | A 30-request read-only burst returned 14 successes and 16 controlled 429 responses |
| Desktop UI | Production styling and text rehearsal inspected in Chrome |

## Budget verification

Concurrent tests exhausted exactly $2 of conservative reservations, including the initial 20 cent safety reserve. Further chat, transcription and speech reservations were refused. Tests also verified that unauthenticated, oversized and exhausted requests never reach the upstream provider. Missing storage fails closed. Tests use isolated temporary databases and do not consume the production allowance.

Live verification calls consume the same production lifetime allowance as visitors. The ledger measures conservative reservations, not actual invoice charges. See [deployment notes](deployment.md) for its scope and model bounds.

## Limits

Synthetic audio was used for verification. No microphone or personal speech was recorded. A human browser microphone conversation and phone-sized rendering were not verified. Browser microphone access still depends on the visitor granting permission.

The production containers were built and exercised by GitHub Actions and Railway. The local Docker engine was unavailable. OpenAI initially rejected calls because the account had no credits; after funding, text feedback and synthetic voice checks succeeded.
