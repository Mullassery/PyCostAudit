/**
 * PyCostAudit Browser Extension - Content Script
 * Injects cost tracking into Claude.ai pages
 */

console.log("[PyCostAudit] Content script loaded");

// Listen for messages from the page
window.addEventListener("message", (event) => {
    if (event.source !== window) return;

    if (event.data.type === "CLAUDE_OPERATION") {
        // Forward operation data to background script
        chrome.runtime.sendMessage(
            {
                type: "TRACK_OPERATION",
                data: event.data.payload,
            },
            (response) => {
                if (chrome.runtime.lastError) {
                    console.error("[PyCostAudit] Error:", chrome.runtime.lastError);
                } else {
                    console.log("[PyCostAudit] Operation tracked:", response);
                }
            }
        );
    }
});

// Inject tracking script
function injectTracker() {
    const script = document.createElement("script");
    script.src = chrome.runtime.getURL("tracker.js");
    script.onload = function () {
        this.remove();
    };
    (document.head || document.documentElement).appendChild(script);
}

// Wait for DOM ready
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", injectTracker);
} else {
    injectTracker();
}
