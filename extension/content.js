// QuoteKeep — content script
// Runs in the page. Its only job is to hand the current text selection
// back to the service worker when the keyboard shortcut is used.
// (The right-click menu already gets the selection from Chrome directly.)

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg && msg.type === "QUOTEKEEP_GET_SELECTION") {
    const text = window.getSelection ? String(window.getSelection()) : "";
    sendResponse({ text });
  }
  // Returning true keeps the message channel open for the async response.
  return true;
});
