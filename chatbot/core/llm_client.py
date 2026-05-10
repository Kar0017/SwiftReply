"""
core/llm_client.py
Groq API client with conversation history support.
Free tier: https://console.groq.com — no credit card required.
Model: llama-3.3-70b-versatile (fast, free, high quality)
"""

import logging
import os
from typing import Any

from groq import Groq

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a helpful customer support assistant for a small business. "
    "Be concise, friendly, and professional. If you don't know something "
    "specific about the business, say so honestly and suggest they contact "
    "support directly."
)

MODEL = "llama-3.3-70b-versatile"

_client: Groq | None = None


def _get_client() -> Groq:
    """Lazily instantiate the Groq client."""
    global _client
    if _client is None:
        _client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    return _client


def get_llm_response(query: str, conversation_history: list[dict[str, Any]]) -> str:
    """
    Call Groq LLM with the last 6 turns of conversation history.

    Args:
        query: The current user message.
        conversation_history: List of {"role": ..., "content": ...} dicts.

    Returns:
        Model's text response, or a graceful fallback string on error.
    """
    recent = conversation_history[-6:] if len(conversation_history) > 6 else conversation_history

    messages: list[dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]

    for turn in recent:
        role = turn.get("role", "user")
        content = turn.get("content", "")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})

    # Append current query if not already the last user turn
    if not messages or messages[-1]["role"] != "user" or messages[-1]["content"] != query:
        messages.append({"role": "user", "content": query})

    try:
        client = _get_client()
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=512,
            temperature=0.7,
        )
        text: str = response.choices[0].message.content
        logger.info(
            "Groq response obtained. Model=%s tokens_used=%s",
            MODEL,
            response.usage.total_tokens,
        )
        return text
    except Exception as exc:  # noqa: BLE001
        logger.exception("Groq API error: %s", exc)
        return "Sorry, I'm having trouble connecting right now. Please try again or contact support@example.com."
