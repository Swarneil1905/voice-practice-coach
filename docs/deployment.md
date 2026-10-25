# Deployment and operations

## Release process

Push changes to main. Inspect the Verify and package workflow. Its publish job advances production only after the backend tests, frontend build, container builds and production smoke tests pass. Railway services follow production. The voice worker uses the agent subdirectory of the voice repository.

After a release, run:

```sh
python deploy/smoke.py https://YOUR-SERVICE.up.railway.app
```

The smoke test verifies real application requests and security headers. It does not spend money on voice or AI calls. Verify those separately with explicit consent. Do not log room tokens, provider keys, transcripts or uploaded photographs.

## Configuration

Use the Railway Variables tab for secrets. Never add real keys to source or GitHub Actions logs. The voice API reads OPENAI_API_KEY for text review unless AI_API_KEY is explicitly supplied. The worker references the API service's LiveKit credentials and VOICE_GATEWAY_SECRET. VOICE_GATEWAY_URL points to the API's /api/provider endpoint. The OpenAI key is used only by the API. Enable voice only after the worker registers successfully.

The voice API uses DATA_DIR=/data for persistent quota counters and its signing key. Do not remove its volume to reset a quota. Set AI_MONTHLY_LIMIT, AI_DAILY_LIMIT, VOICE_MONTHLY_LIMIT and VOICE_DAILY_LIMIT to adjust request counts within the independent lifetime dollar allowance. Periods use UTC.

## Rollback

Use Railway's deployment history to roll back to a known healthy deployment. Inspect the failed run before promoting another commit. Fix forward on main so the next successful publish restores branch consistency. For voice, coordinate rollback of the API and worker if their protocol changes.

## Cost controls

Web services sleep when inactive and have bounded memory. The worker remains connected for incoming calls. Check Railway's workspace usage and configure a spending alert or hard cap appropriate to your other projects. Do not assume the $25 target is enforced by memory limits. OpenAI and LiveKit usage have separate allowances and billing. Keep LiveKit on its free Build plan for this demo.

## Inspection model status

Image quality checks work without a trained model. A meaningful damaged/intact model still requires representative labeled data, held out item-level splits and validation. The application explicitly abstains when no validated model is present; it does not invent defect predictions.

## Shared $2 lifetime allowance

All text and voice calls reserve from the same SQLite ledger before contacting OpenAI. There is no daily or monthly reset and no refund on errors or retries. A 20 cent safety reservation accounts conservatively for initial verification; $1.80 is available for new requests. Reservations use integer microdollars and an atomic conditional update, so concurrent calls cannot overspend the ledger. Missing or inaccessible storage stops paid requests.

| Operation | Fixed model and enforced bound | Reservation |
| --- | --- | --- |
| Text review / voice coaching | gpt-4.1-mini, at most 600 output tokens, bounded input | $0.05 |
| Speech synthesis | tts-1, at most 4,000 characters | $0.10 |
| Speech recognition | whisper-1, PCM WAV at most 60 seconds and 6 MB | $0.02 |

These are conservative per-request cost envelopes, not measured invoice charges. They can exhaust the demo before $2 is billed. They cover the deployed application's OpenAI requests at the reviewed model pricing, not taxes, future provider price changes, Railway, LiveKit, or unrelated uses of the same account/key. Review [OpenAI pricing](https://developers.openai.com/api/docs/pricing) before changing models or request bounds. The gateway ignores caller-selected models, token counts and tools. Never delete or replace the persistent volume to reset spend. A rollback must retain the budgeted API and worker together; rolling back to pre-budget code removes the protection.
