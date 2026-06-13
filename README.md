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



## About this project

QuoteKeep was designed and built collaboratively with Claude (Anthropic's Cowork mode).
The architecture, extension, backend, and reading interface were produced from the
single project brief below.

### Original prompt

> You are an expert Full-Stack Developer and UX/UI Designer. I want you to design and code a web-based "smart note-taking and reading" application for me.
>
> **Project Summary:** I want a system that captures and stores the texts I highlight while browsing websites, similar to taking a screenshot but strictly in "text" format. My goal is absolutely not to open or load the original websites when reading these notes; I just want to read the quotes in a clean and minimalist interface that I host myself.
>
> **Desired Key Features:**
>
> 1. **Text Capture (Browser Extension):** When I select a sentence or paragraph on any web page, I should be able to instantly save this text to my database via a right-click context menu or a keyboard shortcut.
> 2. **Smart Translation Support:** The notes I collect will mostly be in English. However, I will also select texts in Russian, German, or other languages. The system must automatically detect the language of the saved text. If the text is not in English, it should save both the original text and its English translation to the database (via DeepL, Google Translate, or a similar API).
> 3. **Reading Interface (Dashboard):** I want a single-page interface that displays all saved quotes in clean, distraction-free cards. In this interface, notes in foreign languages should be designed to show the original text with the English translation directly underneath it.
> 4. **Source Attribution:** In the bottom right corner of every quote card in the interface, the name or URL of the website from which the text was taken must be written elegantly in a small font. It shouldn't redirect me to that site unless I explicitly click on it.
>
> **My Expectations From You:**
>
> - **Architecture Recommendation:** Determine the most suitable tech stack for this job (e.g., a Chrome Extension for text capture + a lightweight Python/FastAPI-based backend for translation and database management).
> - **Extension Codes:** Write the `manifest.json`, the `content.js` to capture the text, and the `background.js` for background processes for Chrome (or a Chromium-based browser).
> - **Backend & Translation Logic:** Create the core API routes that receive the selected text, detect its language, translate it via an API if necessary, and save it in JSON format.
> - **Frontend Codes:** Provide the HTML/CSS and basic JavaScript for the minimalist quote-reading interface, with a dark mode theme and a typography-focused structure.
> - **Step-by-Step Setup:** Explain step-by-step how to integrate and run all components on localhost.

About this project
QuoteKeep was designed and built collaboratively with Claude (Anthropic's Cowork mode).
The architecture, browser extension, FastAPI backend, and reading interface were all
produced from the single project brief below.

### Original prompt

You are an expert Full-Stack Developer and UX/UI Designer. I want you to design and code a web-based "smart note-taking and reading" application for me.

Project Summary: I want a system that captures and stores the texts I highlight while browsing websites, similar to taking a screenshot but strictly in "text" format. My goal is absolutely not to open or load the original websites when reading these notes; I just want to read the quotes in a clean and minimalist interface that I host myself.


Desired Key Features:
1. Text Capture (Browser Extension): When I select a sentence or paragraph on any web page, I should be able to instantly save this text to my database via a right-click context menu or a keyboard shortcut.

2. Smart Translation Support: The notes I collect will mostly be in English. However, I will also select texts in Russian, German, or other languages. The system must automatically detect the language of the saved text. If the text is not in English, it should save both the original text and its English translation to the database (via DeepL, Google Translate, or a similar API).

3. Reading Interface (Dashboard): I want a single-page interface that displays all saved quotes in clean, distraction-free cards. In this interface, notes in foreign languages should show the original text with the English translation directly underneath it.

4. Source Attribution: In the bottom right corner of every quote card, the name or URL of the website the text was taken from must be written elegantly in a small font. It shouldn't redirect me to that site unless I explicitly click on it.


Expectations: an architecture recommendation, the extension code (manifest.json, content.js, background.js), the backend and translation logic with API routes that detect language and save as JSON, the frontend HTML/CSS/JS for a minimalist dark-mode reading interface, and step-by-step localhost setup.

