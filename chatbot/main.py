# Run instructions:
#   pip install -r requirements.txt
#   Add ANTHROPIC_API_KEY to .env
#   uvicorn main:app --reload --port 8000
#   Visit http://localhost:8000

"""
main.py
FastAPI application entry point.
"""

import os
import sys
from pathlib import Path

# Add current directory to path for Vercel subdirectory support
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from core.logger import setup_logging
from core.rule_engine import load_rules
from router.chat import router as chat_router

load_dotenv()
setup_logging()

app = FastAPI(title="Business Assistant Chatbot", version="1.0.0")

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static files ──────────────────────────────────────────────────────────────
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(chat_router, prefix="/api")

# ── Startup ───────────────────────────────────────────────────────────────────
_rules_count: int = 0


@app.on_event("startup")
async def on_startup() -> None:
    """Load FAQ rules and confirm readiness."""
    global _rules_count
    try:
        _rules_count = load_rules()
        print(f"[OK] Chatbot ready -- {_rules_count} FAQ rules loaded.")
    except Exception as e:
        print(f"[ERROR] Startup rule loading failed: {e}")
        _rules_count = 0


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
async def index() -> FileResponse:
    """Serve the single-page frontend."""
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/api/health")
async def health() -> JSONResponse:
    """Health check endpoint."""
    return JSONResponse({"status": "ok", "rules_loaded": _rules_count})
