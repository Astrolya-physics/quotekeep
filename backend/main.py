"""
QuoteKeep — backend API
A lightweight FastAPI service that:
  1. Receives highlighted text from the browser extension
  2. Detects the language
  3. Translates to English when the text is not already English
  4. Stores everything as JSON
  5. Serves the saved quotes to the reading dashboard

Run with:  uvicorn main:app --reload --port 8000
"""

import json
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from langdetect import detect, DetectorFactory, LangDetectException
from deep_translator import GoogleTranslator

# Make language detection deterministic across runs.
DetectorFactory.seed = 0

# ----------------------------------------------------------------------------
# Paths & storage
# ----------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "notes.json"
FRONTEND_DIR = BASE_DIR.parent / "frontend"

# A simple lock so concurrent saves don't corrupt the JSON file.
_file_lock = threading.Lock()

# Human-readable names for the most common language codes.
LANG_NAMES = {
    "en": "English", "ru": "Russian", "de": "German", "fr": "French",
    "es": "Spanish", "it": "Italian", "pt": "Portuguese", "nl": "Dutch",
    "tr": "Turkish", "pl": "Polish", "uk": "Ukrainian", "sv": "Swedish",
    "ja": "Japanese", "zh-cn": "Chinese", "ko": "Korean", "ar": "Arabic",
    "cs": "Czech", "da": "Danish", "fi": "Finnish", "el": "Greek",
    "no": "Norwegian", "ro": "Romanian", "hu": "Hungarian",
}


def _read_notes() -> list:
    if not DATA_FILE.exists():
        return []
    try:
        with DATA_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _write_notes(notes: list) -> None:
    tmp = DATA_FILE.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(notes, f, ensure_ascii=False, indent=2)
    os.replace(tmp, DATA_FILE)  # atomic on the same filesystem


def _source_label(url: str | None) -> str:
    """Turn a full URL into a clean hostname like 'nytimes.com'."""
    if not url:
        return ""
    try:
        host = urlparse(url).netloc
        return host[4:] if host.startswith("www.") else host
    except Exception:
        return url


# ----------------------------------------------------------------------------
# Request/response models
# ----------------------------------------------------------------------------
class CaptureIn(BaseModel):
    text: str = Field(..., min_length=1)
    url: str | None = None
    title: str | None = None


class Note(BaseModel):
    id: str
    text: str                 # original captured text
    translation: str | None   # English translation (None if already English)
    lang: str                 # detected language code
    lang_name: str            # human-readable language name
    url: str | None
    source: str               # clean hostname for display
    title: str | None
    created_at: str


# ----------------------------------------------------------------------------
# Translation / detection helpers
# ----------------------------------------------------------------------------
def detect_language(text: str) -> str:
    try:
        return detect(text)
    except LangDetectException:
        return "unknown"


def translate_to_english(text: str) -> str | None:
    try:
        return GoogleTranslator(source="auto", target="en").translate(text)
    except Exception as exc:  # network error, rate limit, etc.
        print(f"[translate] failed: {exc}")
        return None


# ----------------------------------------------------------------------------
# App
# ----------------------------------------------------------------------------
app = FastAPI(title="QuoteKeep API", version="1.0.0")

# The extension posts from arbitrary web pages, so allow all origins locally.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/notes", response_model=Note)
def create_note(payload: CaptureIn):
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Empty text")

    lang = detect_language(text)
    translation = None
    if lang != "en":
        translation = translate_to_english(text)

    note = {
        "id": uuid.uuid4().hex,
        "text": text,
        "translation": translation,
        "lang": lang,
        "lang_name": LANG_NAMES.get(lang, lang.upper() if lang else "Unknown"),
        "url": payload.url,
        "source": _source_label(payload.url),
        "title": payload.title,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    with _file_lock:
        notes = _read_notes()
        notes.insert(0, note)  # newest first
        _write_notes(notes)

    return note


@app.get("/api/notes", response_model=list[Note])
def list_notes():
    return _read_notes()


@app.delete("/api/notes/{note_id}")
def delete_note(note_id: str):
    with _file_lock:
        notes = _read_notes()
        new_notes = [n for n in notes if n.get("id") != note_id]
        if len(new_notes) == len(notes):
            raise HTTPException(status_code=404, detail="Note not found")
        _write_notes(new_notes)
    return {"ok": True, "deleted": note_id}


@app.get("/health")
def health():
    return {"status": "ok", "count": len(_read_notes())}


# ----------------------------------------------------------------------------
# Serve the reading dashboard at http://localhost:8000/
# ----------------------------------------------------------------------------
if FRONTEND_DIR.exists():
    @app.get("/")
    def dashboard():
        return FileResponse(FRONTEND_DIR / "index.html")

    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
