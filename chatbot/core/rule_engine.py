"""
core/rule_engine.py
Fuzzy rule matching engine using RapidFuzz.
"""

import json
import logging
import re
import os
from pathlib import Path
from typing import Optional

from rapidfuzz import process, fuzz

logger = logging.getLogger(__name__)

RULES_PATH = Path(__file__).parent.parent / "data" / "rules.json"
THRESHOLD: float = float(os.getenv("FUZZY_MATCH_THRESHOLD", "82"))

GREETINGS = {"hi", "hello", "hey", "thanks", "thank you", "ok", "okay",
             "bye", "goodbye", "yes", "no", "sure", "great", "cool"}

_rules: list[dict] = []
_pattern_map: list[tuple[str, dict]] = []  # (pattern, rule) flat list


def load_rules() -> int:
    """Load rules.json with error handling for deployment environments."""
    global _rules, _pattern_map
    _rules = []
    _pattern_map = []
    
    try:
        if not RULES_PATH.exists():
            logger.warning("Rules file not found at %s. Proceeding with 0 rules.", RULES_PATH)
            return 0
            
        with open(RULES_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Handle both {"rules": [...]} and [...] formats
            _rules = data.get("rules", []) if isinstance(data, dict) else data

        for rule in _rules:
            for pattern in rule["patterns"]:
                _pattern_map.append((pattern.lower().strip(), rule))

        logger.info("Successfully loaded %d rules (%d patterns).", len(_rules), len(_pattern_map))
    except Exception as e:
        logger.error("Failed to load rules: %s", e)
        
    return len(_rules)


def _normalize(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def match_rule(query: str) -> Optional[dict]:
    """
    Find the best fuzzy match for *query* across all FAQ patterns.

    Args:
        query: Raw user input string.

    Returns:
        Matched rule dict (with added ``_score`` key) or None if below threshold.
    """
    if not _pattern_map:
        load_rules()

    normalized = _normalize(query)

    if normalized in GREETINGS:
        return None

    query_words = set(normalized.split())
    if len(query_words) < 4:
        pattern_words = set(word for p, _ in _pattern_map for word in p.split())
        if not query_words.intersection(pattern_words):
            return None

    patterns = [p for p, _ in _pattern_map]

    result = process.extractOne(
        normalized,
        patterns,
        scorer=fuzz.token_set_ratio,
        score_cutoff=THRESHOLD,
    )

    if result is None:
        logger.debug("No match for query=%r (threshold=%.0f).", normalized, THRESHOLD)
        return None

    matched_pattern, score, idx = result
    rule = _pattern_map[idx][1].copy()
    rule["_score"] = score
    rule["_matched_pattern"] = matched_pattern
    logger.info(
        "Rule match: id=%s pattern=%r score=%.1f query=%r",
        rule["id"],
        matched_pattern,
        score,
        normalized,
    )
    return rule
