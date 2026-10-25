# Voice Practice Coach

Practice explaining system design decisions, review the topics you covered, and optionally rehearse with a live voice coach.

[Live demo](https://voice-practice-coach-production.up.railway.app) · [CI](https://github.com/Swarneil1905/voice-practice-coach/actions) · [Architecture](docs/architecture.md) · [Verification notes](docs/verification.md) · [MIT license](LICENSE)

## What you can do

- Choose from three technical scenarios and write a practice response.
- Review topic coverage with supporting quotes from your own answer.
- Request optional AI feedback after explicitly consenting to send the response to a provider.
- Join an optional voice session with microphone controls and an eight minute server enforced limit.

The default review runs locally without an AI account. It checks topic mentions, not whether an explanation is technically correct. Live voice and provider feedback require separate credentials.

## How it works

```text
Angular interface → Django API → Local topic coverage rubric
                              → Optional AI feedback provider
                              → Scoped LiveKit room token
Browser microphone ↔ LiveKit room ↔ Python voice worker
```

| Component | Responsibility |
| --- | --- |
| Angular | Scenarios, response editing, consent, review display and microphone lifecycle |
| Python / Django | Input validation, CSRF protection, review requests and voice access tokens |
| Python / LiveKit | Optional speech recognition, coaching responses and speech synthesis |
| Nginx | Serves the frontend and proxies API requests in Docker |

## Quick start with Docker

Requires Docker Desktop or Docker Engine with Compose. From the repository root:

```sh
docker compose up --build
```

Open **http://localhost:8080**. The default stack runs text practice without external credentials. Stop it with `docker compose down`.

## Run without Docker

Requires Python 3.10+ and Node.js 22.22+. Run these commands from the repository root in PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r api/requirements.txt
.venv\Scripts\python.exe api/manage.py runserver 127.0.0.1:8000
```

In a second terminal:

```sh
cd frontend
npm ci
npm start
```

Open **http://localhost:4200**. On macOS or Linux, use `.venv/bin/python` in place of `.venv\Scripts\python.exe`.

## Optional AI and voice configuration

Copy `.env.example` to `.env` for Docker. For native development, set the variables in the relevant terminals; Django does not load `.env` automatically.

| Variables | Purpose |
| --- | --- |
| `OPENAI_API_KEY` | Provider key held by the API for text and voice |
| `QUOTA_DATABASE` | Persistent SQLite file for the shared paid allowance |
| `VOICE_GATEWAY_URL`, `VOICE_GATEWAY_SECRET` | Worker connection to the budgeted API gateway |
| `ENABLE_VOICE=true` | Enable the voice token endpoint |
| `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET` | Connect the API and worker to the same LiveKit project |

Set a random `VOICE_GATEWAY_SECRET` shared by API and worker. The worker never calls OpenAI directly. The gateway fixes the models and validates text, audio duration and output limits before reserving spend. With credentials configured, start the optional worker through Compose:

```sh
docker compose --profile voice up --build
```

Or install `agent/requirements.txt` into a Python environment and run:

```sh
python agent/worker.py download-files
python agent/worker.py dev
```

Audio leaves the browser only after consent and microphone permission. This application does not record audio; external provider retention policies still apply. Voice tokens expire after 120 seconds for joining, and the worker ends sessions after 480 seconds. The API allows three token requests per hour per observed IP. A separate lifetime ledger caps conservative paid reservations at $2 across all visitors and all paid operations. It never resets by day or month. This application guard does not control unrelated use of your API key or account.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/health` | Service health |
| GET | `/api/capabilities` | Available features and CSRF cookie |
| POST | `/api/practice/review` | Topic coverage or consented provider feedback |
| POST | `/api/voice/token` | Consented access to a scoped voice room |

The browser handles CSRF headers for POST requests. Invalid inputs and provider failures produce explicit errors.

## Development checks

```powershell
.venv\Scripts\python.exe api/manage.py test coach
.venv\Scripts\python.exe -m unittest discover -s agent -p 'test_*.py'
cd frontend
npm run build
```

GitHub Actions runs API and deadline tests, frontend and container builds, and production HTTP smoke tests before promoting the tested commit for Railway. Live audio and paid provider calls require manual verification with configured credentials. See the [verification notes](docs/verification.md) for the recorded local checks and limitations.

## Repository guide

| Path | Contents |
| --- | --- |
| `frontend/src/practice.ts` | Practice flow, consent and microphone controls |
| `api/coach/views.py` | Request handling, validation and provider integration |
| `api/coach/rubric.py` | Local coverage rules |
| `agent/` | Voice worker and session deadline tests |
| `docs/` | Architecture, design provenance and verification details |

The public demo uses a bounded Nginx gateway and persistent paid usage allowances. See [deployment and operations](docs/deployment.md) for the release process, quota settings and rollback.

## License

Original project code is licensed under the [MIT License](LICENSE), copyright © 2026 Swarneil Pradhan. Bundled DM Sans and Instrument Serif fonts retain their SIL Open Font Licenses in [`frontend/public/fonts`](frontend/public/fonts). Third party dependencies retain their respective licenses.
