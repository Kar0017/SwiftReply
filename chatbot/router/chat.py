"""
router/chat.py
POST /api/chat — hybrid rule-based + LLM chat endpoint.
"""

import logging
from typing import Any, Literal, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from core import llm_client, rule_engine
from core.logger import log_conversation, read_recent_logs

router = APIRouter()
logger = logging.getLogger(__name__)


# ── Request / Response schemas ────────────────────────────────────────────────

class Message(BaseModel):
    """Single conversation turn."""
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    """Incoming chat payload from the frontend."""
    message: str = Field(..., min_length=1, max_length=4096)
    session_id: str = Field(..., min_length=1)
    conversation_history: list[Message] = Field(default_factory=list)


class ChatResponse(BaseModel):
    """Response sent back to the frontend."""
    response: str
    response_type: Literal["rule_based", "llm"]
    matched_rule_id: Optional[str] = None
    session_id: str


class FeedbackRequest(BaseModel):
    session_id: str
    message: str
    rating: str  # "up" or "down"


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Hybrid chat endpoint.

    1. Try fuzzy rule matching.
    2. If matched → return FAQ response.
    3. Else → call Claude LLM.
    4. Log the interaction.
    """
    message = request.message.strip()
    history: list[dict[str, Any]] = [m.model_dump() for m in request.conversation_history]

    matched_rule = rule_engine.match_rule(message)

    if matched_rule:
        response_text: str = matched_rule["response"]
        response_type: Literal["rule_based", "llm"] = "rule_based"
        matched_rule_id: Optional[str] = matched_rule["id"]
        fuzzy_score: Optional[float] = matched_rule.get("_score")
        logger.info("Rule hit: %s (score=%.1f)", matched_rule_id, fuzzy_score or 0)
    else:
        response_text = llm_client.get_llm_response(message, history)
        response_type = "llm"
        matched_rule_id = None
        fuzzy_score = None
        logger.info("LLM fallback used for session=%s", request.session_id[:8])

    log_conversation(
        session_id=request.session_id,
        user_message=message,
        bot_response=response_text,
        response_type=response_type,
        matched_rule_id=matched_rule_id,
        fuzzy_score=fuzzy_score,
    )

    return ChatResponse(
        response=response_text,
        response_type=response_type,
        matched_rule_id=matched_rule_id,
        session_id=request.session_id,
    )


@router.get("/logs")
async def get_logs(n: int = 50) -> dict:
    """Return the last *n* conversation log entries (default 50)."""
    entries = read_recent_logs(n=min(n, 200))
    return {"count": len(entries), "entries": entries}


@router.post("/feedback")
async def feedback(req: FeedbackRequest):
    logger.info(f"Feedback [{req.rating}] for session {req.session_id}")
    return {"ok": True}
