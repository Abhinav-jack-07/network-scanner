from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse

from whatsapp_bot.config import get_settings
from whatsapp_bot.state import StateStore

settings = get_settings()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("whatsapp-bot")

app = FastAPI(title="WhatsApp AI Chatbot")
state_store = StateStore(
    max_history=settings.max_history,
    rate_limit_window_seconds=settings.rate_limit_window_seconds,
    rate_limit_max=settings.rate_limit_max,
)

OPT_OUT_KEYWORDS = {"stop", "unsubscribe", "opt out"}
OPT_IN_KEYWORDS = {"start", "subscribe", "opt in"}
HUMAN_KEYWORDS = {"human", "agent", "representative", "support"}
HELP_KEYWORDS = {"help", "menu"}

SYSTEM_PROMPT = (
    "You are the {business} WhatsApp assistant. Reply concisely in the same language as the user. "
    "If you are unsure, say you will connect them with a human. "
    "Do not request or store sensitive personal data. "
    "If the user requests to opt out, confirm it and stop messaging."
)

FALLBACK_MESSAGE = (
    "I am having trouble responding right now. Reply HUMAN to connect with a person."
)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def _verify_signature(signature_header: Optional[str], body: bytes) -> bool:
    if not signature_header:
        return False
    digest = hmac.new(
        settings.whatsapp_app_secret.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()
    expected = f"sha256={digest}"
    return hmac.compare_digest(signature_header, expected)


def _load_faq() -> List[Dict[str, Any]]:
    try:
        with open(settings.faq_path, "r", encoding="utf-8") as faq_file:
            return json.load(faq_file)
    except FileNotFoundError:
        logger.warning("FAQ file not found at %s", settings.faq_path)
        return []


FAQ_ENTRIES = _load_faq()


def _match_faq(message_text: str) -> Optional[str]:
    normalized = _normalize(message_text)
    for entry in FAQ_ENTRIES:
        for question in entry.get("questions", []):
            if question in normalized:
                return entry.get("answer")
    return None


def _extract_messages(payload: Dict[str, Any]) -> List[Dict[str, str]]:
    messages: List[Dict[str, str]] = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for message in value.get("messages", []):
                if message.get("type") != "text":
                    continue
                text = message.get("text", {}).get("body", "")
                messages.append(
                    {
                        "from": message.get("from", ""),
                        "id": message.get("id", ""),
                        "text": text,
                    }
                )
    return messages


def _redact_for_logs(text: str) -> str:
    if not text:
        return ""
    limit = settings.log_redaction_chars
    redacted = text[:limit]
    if len(text) > limit:
        redacted += "…"
    return redacted


async def _send_text_message(to_number: str, text: str) -> None:
    url = (
        "https://graph.facebook.com/"
        f"{settings.whatsapp_api_version}/{settings.whatsapp_phone_number_id}/messages"
    )
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"preview_url": False, "body": text},
    }
    headers = {"Authorization": f"Bearer {settings.whatsapp_access_token}"}
    async with httpx.AsyncClient(
        timeout=settings.whatsapp_request_timeout_seconds
    ) as client:
        response = await client.post(url, headers=headers, json=payload)
        if response.status_code >= 400:
            logger.error(
                "WhatsApp API error: %s %s", response.status_code, response.text
            )
            response.raise_for_status()


async def _generate_ai_response(user_id: str, user_text: str) -> str:
    user_state = state_store.get(user_id)
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT.format(business=settings.business_name),
        },
        *user_state.history,
        {"role": "user", "content": user_text},
    ]
    payload = {
        "model": settings.openai_model,
        "messages": messages,
        "temperature": 0.2,
    }
    headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
    async with httpx.AsyncClient(
        timeout=settings.openai_request_timeout_seconds
    ) as client:
        response = await client.post(
            f"{settings.openai_base_url}/chat/completions",
            headers=headers,
            json=payload,
        )
        if response.status_code >= 400:
            logger.error("OpenAI error: %s %s", response.status_code, response.text)
            return FALLBACK_MESSAGE
        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            return FALLBACK_MESSAGE
        return choices[0].get("message", {}).get("content", FALLBACK_MESSAGE)


@app.get("/health")
async def health_check() -> JSONResponse:
    return JSONResponse({"status": "ok"})


@app.get("/webhook")
async def verify_webhook(request: Request) -> PlainTextResponse:
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    if mode == "subscribe" and token == settings.whatsapp_verify_token:
        return PlainTextResponse(challenge or "")
    raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/webhook")
async def handle_webhook(request: Request) -> JSONResponse:
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")
    if not _verify_signature(signature, body):
        raise HTTPException(status_code=403, detail="Invalid signature")
    payload = await request.json()
    messages = _extract_messages(payload)
    if not messages:
        return JSONResponse({"status": "ignored"})

    for message in messages:
        user_id = message["from"]
        user_text = message["text"]
        normalized = _normalize(user_text)
        user_state = state_store.get(user_id)
        state_store.record_message(user_state)

        logger.info(
            "Incoming message from %s: %s", user_id, _redact_for_logs(user_text)
        )

        if normalized in OPT_OUT_KEYWORDS:
            user_state.opted_out = True
            user_state.human_handoff = False
            await _send_text_message(user_id, "You are opted out. Reply START to resume.")
            continue

        if normalized in OPT_IN_KEYWORDS:
            user_state.opted_out = False
            user_state.human_handoff = False
            await _send_text_message(user_id, "Thanks! You are opted back in.")
            continue

        if user_state.opted_out:
            await _send_text_message(
                user_id, "You are opted out. Reply START to opt back in."
            )
            continue

        if normalized in HELP_KEYWORDS:
            await _send_text_message(
                user_id,
                "Reply with your question, send HUMAN for a person, or STOP to opt out.",
            )
            continue

        if normalized in HUMAN_KEYWORDS:
            user_state.human_handoff = True
            await _send_text_message(
                user_id,
                "Got it. A human agent will follow up shortly. Reply START to return to the AI assistant.",
            )
            continue

        if user_state.human_handoff:
            await _send_text_message(
                user_id,
                "A human agent will follow up shortly. Reply START to return to the AI assistant.",
            )
            continue

        if state_store.is_rate_limited(user_state):
            await _send_text_message(
                user_id, "You are sending messages too quickly. Please slow down."
            )
            continue

        faq_answer = _match_faq(user_text)
        if faq_answer:
            state_store.add_history(user_state, "user", user_text)
            state_store.add_history(user_state, "assistant", faq_answer)
            await _send_text_message(user_id, faq_answer)
            continue

        ai_response = await _generate_ai_response(user_id, user_text)
        state_store.add_history(user_state, "user", user_text)
        state_store.add_history(user_state, "assistant", ai_response)
        await _send_text_message(user_id, ai_response)

    return JSONResponse({"status": "ok"})
