"""Authenticated voice provider gateway. Every upstream attempt reserves budget first."""
import hmac
import io
import json
import logging
import os
import wave
import httpx
from django.http import HttpResponse, JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .budget import reserve_cost


def failure(message, status):
    return JsonResponse({"error": {"message": message, "type": "demo_budget", "code": "demo_budget"}}, status=status)


@csrf_exempt
@require_POST
def provider(request, operation):
    secret = os.getenv("VOICE_GATEWAY_SECRET", "")
    supplied = request.headers.get("X-Voice-Worker-Key", "")
    if not secret or not hmac.compare_digest(secret, supplied):
        return failure("Worker authentication required.", 403)
    key = os.getenv("OPENAI_API_KEY", "")
    if not key:
        return failure("Provider unavailable.", 503)
    try:
        if operation == "audio/transcriptions":
            upload = request.FILES.get("file")
            if not upload or upload.size > 6_000_000:
                return failure("Send a WAV segment under 60 seconds.", 400)
            audio = upload.read()
            with wave.open(io.BytesIO(audio)) as wav:
                if wav.getnchannels() > 2 or wav.getframerate() < 8000 or wav.getnframes() / wav.getframerate() > 60:
                    return failure("Audio segment exceeds demo limits.", 400)
            kwargs = {"data": {"model": "whisper-1", "language": "en", "response_format": "verbose_json"}, "files": {"file": ("speech.wav", audio, "audio/wav")}}
            charge = "transcription"
        elif operation in {"chat/completions", "audio/speech"}:
            if len(request.body) > 32768:
                return failure("Request exceeds demo limits.", 400)
            body = json.loads(request.body)
            if not isinstance(body, dict):
                return failure("Send a JSON object.", 400)
            if operation == "chat/completions":
                messages = body.get("messages")
                if not isinstance(messages, list) or not 1 <= len(messages) <= 40:
                    return failure("Conversation exceeds demo limits.", 400)
                clean = []
                for message in messages:
                    if not isinstance(message, dict) or message.get("role") not in {"system", "developer", "user", "assistant"} or not isinstance(message.get("content"), str):
                        return failure("Only text conversation is supported.", 400)
                    clean.append({"role": message["role"], "content": message["content"]})
                kwargs = {"json": {"model": "gpt-4.1-mini", "messages": clean, "max_tokens": 600, "stream": True}}
                charge = "chat"
            else:
                text = body.get("input")
                if not isinstance(text, str) or not 1 <= len(text) <= 4000:
                    return failure("Speech exceeds demo limits.", 400)
                kwargs = {"json": {"model": "tts-1", "voice": "alloy", "input": text, "response_format": "pcm", "speed": 1.0}}
                charge = "speech"
        else:
            return failure("Unsupported provider operation.", 404)
    except (ValueError, TypeError, AttributeError, wave.Error, EOFError):
        return failure("Invalid provider input.", 400)
    if not reserve_cost(charge):
        return failure("The shared paid demo allowance is exhausted. Use free text practice.", 429)
    client = httpx.Client(timeout=30, follow_redirects=False)
    try:
        outgoing = client.build_request("POST", "https://api.openai.com/v1/" + operation, headers={"Authorization": "Bearer " + key}, **kwargs)
        response = client.send(outgoing, stream=True)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        logging.getLogger(__name__).warning("Voice provider failed: %s", type(exc).__name__)
        client.close()
        return failure("Voice provider unavailable.", 502)
    def content():
        try:
            yield from response.iter_bytes()
        finally:
            response.close()
            client.close()
    result = StreamingHttpResponse(content(), content_type=response.headers.get("content-type", "application/octet-stream"))
    result["Cache-Control"] = "no-store"
    return result
