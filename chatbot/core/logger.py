"""
core/logger.py
Append-only JSONL conversation logger + console logging setup.
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

LOGS_DIR = Path(__file__).parent.parent / "logs"
LOG_FILE = LOGS_DIR / "conversations.jsonl"

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    """Configure root logger to INFO with a readable console format."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )


def log_conversation(
    session_id: str,
    user_message: str,
    bot_response: str,
    response_type: str,
    matched_rule_id: Optional[str] = None,
    fuzzy_score: Optional[float] = None,
) -> None:
    """
    Append one conversation turn to conversations.jsonl.

    Args:
        session_id: Client-generated UUID for the session.
        user_message: Raw user input.
        bot_response: Bot's reply text.
        response_type: ``"rule_based"`` or ``"llm"``.
        matched_rule_id: FAQ rule id if rule_based, else None.
        fuzzy_score: RapidFuzz match score if rule_based, else None.
    """
    entry: dict = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
        "session_id": session_id,
        "user_message": user_message,
        "bot_response": bot_response,
        "response_type": response_type,
        "matched_rule_id": matched_rule_id,
        "fuzzy_score": round(fuzzy_score, 2) if fuzzy_score is not None else None,
    }

    try:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        logger.warning("Could not write to log file (read-only filesystem): %s", e)

    logger.info(
        "Logged | session=%s type=%s rule=%s score=%s",
        session_id[:8],
        response_type,
        matched_rule_id,
        fuzzy_score,
    )


def read_recent_logs(n: int = 50) -> list[dict]:
    """
    Read the last *n* entries from conversations.jsonl.

    Args:
        n: Max entries to return.

    Returns:
        List of log entry dicts, most recent last.
    """
    if not LOG_FILE.exists():
        return []

    lines: list[str] = LOG_FILE.read_text(encoding="utf-8").splitlines()
    recent = lines[-n:] if len(lines) > n else lines

    entries: list[dict] = []
    for line in recent:
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                logger.warning("Skipping malformed log line.")
    return entries
