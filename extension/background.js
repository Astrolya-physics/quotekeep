// QuoteKeep — service worker (MV3)
// Responsibilities:
//   - register the right-click context menu
//   - handle the keyboard shortcut
//   - POST captured text to the local backend
//   - show a small confirmation notification

const API_URL = "http://localhost:8000/api/notes";

// --- Create the context menu once on install -------------------------------
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "quotekeep-save",
    title: "Save to QuoteKeep",
    contexts: ["selection"], // only shows when text is selected
  });
});

// --- Right-click menu click -------------------------------------------------
chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "quotekeep-save" && info.selectionText) {
    saveQuote(info.selectionText, tab);
  }
});

// --- Keyboard shortcut (Ctrl/Cmd+Shift+S) -----------------------------------
chrome.commands.onCommand.addListener(async (command) => {
  if (command !== "save-selection") return;

  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab || !tab.id) return;

  // Ask the content script for the current selection.
  chrome.tabs.sendMessage(tab.id, { type: "QUOTEKEEP_GET_SELECTION" }, (resp) => {
    if (chrome.runtime.lastError) {
      notify("QuoteKeep", "Could not read selection on this page.");
      return;
    }
    const text = resp && resp.text ? resp.text.trim() : "";
    if (text) {
      saveQuote(text, tab);
    } else {
      notify("QuoteKeep", "No text selected.");
    }
  });
});

// --- Core: send the quote to the backend ------------------------------------
async function saveQuote(text, tab) {
  const payload = {
    text: text,
    url: tab ? tab.url : null,
    title: tab ? tab.title : null,
  };

  try {
    const res = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) throw new Error("HTTP " + res.status);

    const note = await res.json();
    const wasTranslated = note.translation ? ` (${note.lang_name} → English)` : "";
    notify("Saved to QuoteKeep", `"${truncate(text, 80)}"${wasTranslated}`);
  } catch (err) {
    notify(
      "QuoteKeep — save failed",
      "Is the backend running on localhost:8000? " + err.message
    );
  }
}

function truncate(s, n) {
  return s.length > n ? s.slice(0, n - 1) + "…" : s;
}

function notify(title, message) {
  // Notifications need an icon in some Chrome builds; fall back gracefully.
  chrome.notifications.create(
    {
      type: "basic",
      iconUrl:
        "data:image/svg+xml;base64," +
        btoa(
          '<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128">' +
            '<rect width="128" height="128" rx="24" fill="#7c8cff"/>' +
            '<text x="64" y="86" font-size="72" text-anchor="middle" fill="#0d0d12" font-family="Georgia">"</text>' +
            "</svg>"
        ),
      title,
      message,
    },
    () => void chrome.runtime.lastError // swallow icon errors silently
  );
}
