# Fieldwork Practice

A technical practice workspace with three system design scenarios. Angular handles the room, Python/Django provides review and token endpoints, and a Python LiveKit worker supports optional voice conversations.

## Run locally

Open this folder in Cursor or open the parent Fieldwork.code-workspace.

### Docker

Start Docker Desktop, then run `docker compose up --build` from this folder. Open http://localhost:8080. The voice worker is optional and is excluded from the default build.

### Native development

Requires Python 3.10 or newer and Node.js 22.22 or newer.

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r api/requirements.txt
.venv\Scripts\python.exe api/manage.py runserver 127.0.0.1:8000
```

In a second terminal:

```powershell
cd frontend
npm ci
npm start
```

Open http://localhost:4200. No external account is needed for local coverage review. The baseline checks topic mentions and cites the learner's text; it does not grade technical correctness.

## Optional AI and voice

Copy .env.example to .env for Docker, or set the equivalent environment variables in native terminals. Never commit actual credentials. Native Django does not automatically read .env files.

For text AI feedback, set AI_API_KEY, AI_BASE_URL and AI_MODEL. The interface reveals an explicit consent option when configured. Provider failure is visible and does not produce fabricated feedback.

For voice, create a LiveKit project, configure LIVEKIT_URL, LIVEKIT_API_KEY and LIVEKIT_API_SECRET, set OPENAI_API_KEY for the worker, and set ENABLE_VOICE=true on the API. Install agent/requirements.txt, run `python agent/worker.py download-files`, then `python agent/worker.py dev` with the same LiveKit credentials. In Docker use `docker compose --profile voice up --build`.

Audio is transmitted to LiveKit and configured speech/model providers only after consent and microphone permission. The worker enforces a 480 second session deadline independently of the browser. Token lifetime is 120 seconds and controls joining only. Three token requests per hour per API-observed IP limits local use; it is not an account billing cap. Set actual provider spending limits before paid testing.

## Tests

```powershell
.venv\Scripts\python.exe api/manage.py test coach
.venv\Scripts\python.exe -m unittest discover -s agent -p 'test_*.py'
cd frontend
npm run build
```

Verified locally: production frontend build, 10 Django tests, 3 worker deadline tests, worker SDK import, and browser text review against the API. Live audio and paid AI provider calls have not been exercised because credentials are not configured. No audio is recorded by this code. External provider retention policies still apply.

## Code map

* frontend/src/practice.ts: scenario, consent, microphone lifecycle and review interface.
* api/coach/views.py: validation, CSRF, rate limits, optional provider calls and scoped LiveKit token.
* api/coach/rubric.py: transparent topic coverage baseline.
* agent/worker.py and agent/session_limit.py: voice coaching and server deadline.
* docs/: architecture, research provenance and REA evidence.
* .github/workflows/ci.yml: verification only, no deployment.

Docker Compose configuration validates, but image builds were not run because the local Docker daemon is unavailable. This is a local single-user edition. Railway deployment remains deferred.
