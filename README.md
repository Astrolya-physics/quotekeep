# QuoteKeep

A self-hosted, text-only highlight keeper. Select text on any web page, save it with one
click or shortcut, and read all your quotes later in a clean, distraction-free dark interface —
without ever reopening the original sites. Non-English quotes are auto-detected and stored with
an English translation shown directly beneath the original.

## Architecture

```
┌─────────────────────┐   POST text + url    ┌──────────────────────┐
│  Chrome extension   │ ───────────────────▶ │  FastAPI backend     │
│  (capture)          │                      │  • detect language   │
│  • right-click menu │                      │  • translate → EN    │
│  • Ctrl+Shift+S     │                      │  • save to notes.json│
└─────────────────────┘                      └──────────┬───────────┘
                                                         │ serves
                                              ┌──────────▼───────────┐
                                              │  Dashboard (HTML/JS) │
                                              │  localhost:8000      │
                                              └──────────────────────┘
```

**Stack chosen for your workflow:**
- **Capture** — a Manifest V3 Chrome/Chromium extension (works in Chrome, Edge, Brave, Arc).
- **Backend** — Python + FastAPI. Tiny, fast, one file.
- **Translation** — `deep-translator` against Google Translate's free endpoint. No API key, no signup.
- **Language detection** — `langdetect`.
- **Storage** — a single human-readable `notes.json` file (newest first). Easy to back up or grep.
- **Frontend** — one static `index.html`, typography-first dark theme, served by the backend itself.

```
quotekeep/
├── backend/
│   ├── main.py            # API + serves the dashboard
│   ├── requirements.txt
│   └── notes.json         # created automatically on first save
├── extension/
│   ├── manifest.json
│   ├── background.js      # context menu, shortcut, POST to backend
│   └── content.js         # reads the page text selection
└── frontend/
    └── index.html         # the reading dashboard
```

## Setup (localhost)

### 1. Run the backend

```bash
cd quotekeep/backend
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Leave this terminal running. Open **http://localhost:8000/** in your browser — you should see the
empty QuoteKeep dashboard. (API docs are at http://localhost:8000/docs.)

### 2. Load the extension

1. Open `chrome://extensions` (or `edge://extensions`, `brave://extensions`).
2. Toggle **Developer mode** on (top-right).
3. Click **Load unpacked** and select the `quotekeep/extension` folder.
4. QuoteKeep now appears in your extensions list.

### 3. Save your first quote

- Select any text on a web page → **right-click → "Save to QuoteKeep"**, **or** select text and press
  **Ctrl+Shift+S** (Cmd+Shift+S on Mac).
- A small notification confirms the save (and tells you if it was translated).
- Open / refresh **http://localhost:8000/** to read it. The dashboard also auto-refreshes when you
  return to the tab.

> The keyboard shortcut can be changed at `chrome://extensions/shortcuts`.

## How it behaves

- **English text** is stored as-is.
- **Non-English text** (Russian, German, etc.) is detected automatically; the original is stored
  along with an English translation, shown beneath it on the card.
- **Source** (the site's hostname) sits quietly in the bottom-right of each card. It only navigates
  to the original page if you actually click it (opens in a new tab).
- Hover a card to reveal a **×** to delete it.
- Use the search box to filter across originals, translations, and sources.

## Notes & troubleshooting

- **"Save failed" notification** → the backend isn't running, or not on port 8000. Start uvicorn first.
- **Translation didn't happen** → the free Google endpoint occasionally rate-limits. The original is
  always saved regardless; only the translation is skipped (logged in the backend terminal).
- **Your data** lives entirely in `backend/notes.json` on your machine. Nothing leaves your computer
  except the text sent to the translation endpoint for non-English quotes.
- **Want DeepL instead?** Swap the `translate_to_english` function in `main.py` for the DeepL client
  and add your key — the rest of the system is unchanged.

## API reference

| Method | Route             | Purpose                                  |
|--------|-------------------|------------------------------------------|
| POST   | `/api/notes`      | Save `{text, url, title}`; returns the stored note |
| GET    | `/api/notes`      | List all notes (newest first)            |
| DELETE | `/api/notes/{id}` | Delete a note                            |
| GET    | `/health`         | Health check + note count                |
| GET    | `/`               | The reading dashboard                    |
```
